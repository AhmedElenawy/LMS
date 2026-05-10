from education.redis_client import r
import hashlib
import secrets
from .tasks import send_email


class Otp:
    def __init__ (self,email, purpose):
        self.email = email
        self.purpose = purpose
        self.key = f"otp:{email}:{purpose}"
        self.rate_limit_key = f"rate_limit:{email}:{purpose}"
        self.expire = (5 * 60) - 5
        self.max_attempts = 3

    def hash_otp(self, otp):
        return hashlib.sha256(str(otp).encode()).hexdigest()

    def generate_otp(self):
        # Use atomic lock to prevent duplicate OTP jobs under concurrent requests.
        lock_acquired = r.set(self.rate_limit_key, "True", ex=118, nx=True)
        if not lock_acquired:
            raise Exception("you have already requested an otp. please wait for 2 minutes")

        otp = secrets.randbelow(900000) + 100000
        r.hset(self.key, mapping={
            "otp":self.hash_otp(otp),
            "attempts":"0",
            "verified":"False"
        })

        r.expire(self.key, self.expire)
        return otp
    
    def send_otp(self):
        otp = self.generate_otp()
        try:
            send_email.delay(otp, self.purpose, self.email)
        except Exception:
            # Roll back so user can retry when enqueue/send fails.
            self.delete_otp()
            raise Exception("Failed to queue OTP email. Please try again.")
        return otp

    

    
    def get_otp_data(self):
        data = r.hgetall(self.key)
        return {
            "otp":data.get("otp"),
            "attempts":int(data.get("attempts")),    
            "verified":data.get("verified") == "True"
        }
    
    def check_key(self):
        return r.exists(self.key)
    

    def validate_otp(self, user_otp):
        if not self.check_key():
            raise Exception("OTP has been expired or dont exist")
        
        data = self.get_otp_data()
        # may session has been exoired between chack and get
        if not data:
            raise Exception("OTP has expired")

        if data["attempts"] >= self.max_attempts:
            raise Exception("you reach maximum attempts. please try after 5 minutes")
        
        if data["verified"]:
            raise Exception("OTP has been already verified")
        # for better security prevent timing attacks
        if secrets.compare_digest(data["otp"], self.hash_otp(user_otp)):
            r.hset(self.key, "verified", "True")
            # password still not validated
            # r.delete(self.rate_limit_key)
            # r.delete(self.key)
            return True
        
        new_attempts = r.hincrby(self.key, "attempts", 1)
        raise Exception(f"Invalid OTP you have {self.max_attempts - new_attempts} attempts left")


    def delete_otp(self):
        r.delete(self.key)
        r.delete(self.rate_limit_key)

        
    

