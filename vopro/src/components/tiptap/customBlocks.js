import { Node } from "@tiptap/core";

export const CustomBlock = Node.create({
  name: "customBlock",

  group: "block",
  content: "block+",       // <-- FIX: allows paragraphs, images, tables, ANY block content
  draggable: true,
  isolating: true,

  addAttributes() {
    return {
      variant: {
        default: "card",
        parseHTML: el => el.getAttribute("variant"),
        renderHTML: attrs => {
          return { variant: attrs.variant };
        },
      },
      image: {
        default: null,
      },
    };
  },

  parseHTML() {
    return [{ tag: "custom-block" }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "custom-block",
      HTMLAttributes,
      0, // MUST be last
    ];
  },
  addNodeView() {
    return ({ node, editor, getPos }) => {
      const dom = document.createElement("div");
      dom.className = "custom-block-wrapper";

      const contentDOM = document.createElement("div");
      contentDOM.className = "custom-block-content";

      const deleteBtn = document.createElement("button");
      deleteBtn.className = "custom-block-delete-btn";
      deleteBtn.innerText = "✖";

      deleteBtn.addEventListener("click", () => {
        const pos = getPos();
        editor.chain().focus().deleteRange({ from: pos, to: pos + node.nodeSize }).run();
      });

      dom.appendChild(deleteBtn);
      dom.appendChild(contentDOM);

      return {
        dom,
        contentDOM,
      };
    };
  },
});
