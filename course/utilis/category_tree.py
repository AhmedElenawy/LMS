
def build_tree(nodes):
    # the acual tree build
    tree = []
    # the current path
    stack = []

    for node in nodes:
        item = {
            "id": node.id,
            "title": node.title,
            "slug": node.slug,
            "children": []
        }
        # filter the stack to choose right parent removing cousins and siblings
        while stack and stack[-1]["level"] >= node.level:
            stack.pop()

        if stack:
            #  add children to parent
            # both list have reference to same object
            stack[-1]["children"].append(item)
        else:
            # it will append only the grandparet(root)
            tree.append(item)

        item["level"] = node.level
        # put the item in the path to update it
        stack.append(item)

    return tree