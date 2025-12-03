import React, { useCallback, useEffect  } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import { ResizableImage } from "./tiptap/ResizableImage";
import Mention from "@tiptap/extension-mention";
/*import Table from "@tiptap/extension-table";*/
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import CharacterCount from "@tiptap/extension-character-count";
import Color from "@tiptap/extension-color";

import Highlight from "@tiptap/extension-highlight";
/*import TextStyle from "@tiptap/extension-text-style";*/

import { mentionConfig } from "./tiptap/mention";
import { CustomBlock } from "./tiptap/customBlocks";
import "./richTextEditor.css";

import { Node } from "@tiptap/core";

const CardBlock = Node.create({
  name: "cardBlock",
  group: "block",
  content: "inline*",
  parseHTML() {
    return [{ tag: "card-block" }];
  },
  renderHTML({ HTMLAttributes }) {
    return [
      "card-block", 
      HTMLAttributes,
      0,
      ];
  },
});

export const BannerBlock = Node.create({
  name: "bannerBlock",
  group: "block",
  content: "inline*",
  draggable: true,
  addAttributes() {
    return {
      image: { default: null },
      variant: { default: "banner" },
    };
  },
  parseHTML() {
    return [{ tag: "banner-block" }];
  },
  renderHTML({ HTMLAttributes }) {
    return [
      "banner-block",
      HTMLAttributes,
      0,
    ];
  }
,
});
/*export const TableBlock = Node.create({
  name: "tableBlock",
  group: "block",
  content: "table",
  draggable: true,

  parseHTML() {
    return [{ tag: "table-block" }];
  },

  renderHTML() {
    return ["table-block", 0];
  },
});
*/

export default function RichTextEditor({ value, onChange }) {
    
    const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,
        code: false,
      }),
      Underline,
      ResizableImage,
      CustomBlock,
      Mention.configure({ HTMLAttributes: { class: "mention" }, suggestion: mentionConfig }),
      /*Table.configure({ resizable: true }),*/
      TableRow,
      TableCell,
      TableHeader,
      CharacterCount.configure({ limit: 5000 }),
      Color.configure({ types: ["textStyle"] }),
      /*Highlight,*/
      /*TextStyle,*/
      BannerBlock,
      CardBlock,
      Mention.configure({
        HTMLAttributes: { class: "mention" },
        suggestion: {
          items: (query) =>
            ["AI Assistant", "Support Bot", "Admin"].filter((item) =>
              item.toLowerCase().includes(query.toLowerCase())
            ),
        },
      }),
    ],
    content: value && value.trim() !== "" ? value : "<p>Start typing...</p>",
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });
   // When editor is created and content was empty, focus + set caret at start
  useEffect(() => {
    if (!editor) return;

    // focus editor and set selection to start if we inserted a blank paragraph
    const isEmpty = !value || value.trim() === "";
    if (isEmpty) {
      // slight delay to allow editor to mount DOM
      setTimeout(() => {
        try {
          editor.chain().focus().setTextSelection(1).run(); // position caret inside first paragraph
        } catch (err) {
          // fallback: just focus
          editor.chain().focus().run();
        }
      }, 30);
    }
  }, [editor, value]);

  if (!editor) return null;

  const uploadImage = (file) => {
    const reader = new FileReader();
    reader.onload = () => {
      editor.chain().focus().setImage({ src: reader.result }).run();
    };
    reader.readAsDataURL(file);
  };
  
  const insertImage = useCallback(() => {
    const url = window.prompt("Image URL:");
    if (url) editor?.chain().focus().setImage({ src: url }).run();
  }, [editor]);

const addBold = () => {
editor.chain().focus().toggleBold().run();
};
const addItalic = () => {
editor.chain().focus().toggleItalic().run();
};
const addUnderline = () => {
editor.chain().focus().toggleUnderline().run();
};

const addHeader1 = () => {
editor.chain().focus().toggleHeading({ level: 1 }).run();
};
const addHeader2 = () => {
editor.chain().focus().toggleHeading({ level: 2 }).run();
};
const addBulletList = () => {
editor.chain().focus().toggleBulletList().run();
};
const addOrderedList = () => {
editor.chain().focus().toggleOrderedList().run();
};
const addPage = () => {
editor.chain().focus().insertContent("<p></p>").run();
};
const addCard = () => {
editor.chain().focus().insertContent({
  type: "customBlock",
  attrs: { variant: "card" },
  content: [
    { type: "paragraph", content: [{ type: "text", text: "Card content…" }] }  ]}).run();
};

const addBanner = () => {
editor
.chain()
.focus()
.insertContent(`
  <custom-block variant="banner">
    <p>Banner description...</p>
  </custom-block>
`).run();
};
const addFAQ = () => {
editor.chain().focus().insertContent({
  type: "customBlock",
  attrs: { variant: "faq" },
  content: [
    { type: "paragraph", content: [{ type: "text", text: "Question…" }] },
    { type: "paragraph", content: [{ type: "text", text: "Answer…" }] },
  ]
}).run();
};
const addTable = () => {
editor.chain().focus().insertTable({ rows: 3, cols: 3 }).run();
};
const deleteNode = () => {
editor.chain().focus().deleteSelection().run();
};
  return (
    <div className="tiptap-wrapper">

      {/* Toolbar */}
      <div className="tiptap-toolbar">
      
        {/* Formatting */}
        <button onClick={addBold }className={editor.isActive("bold") ? "active" : ""}><span>🅱️</span> Bold</button>
        <button onClick={addItalic}className={editor.isActive("italic") ? "active" : ""}><span>𝘐</span> Italic</button>
        <button onClick={addUnderline} className={editor.isActive("underline") ? "active" : ""}><span>▁</span> Underline</button>
        
        {/* Headings */}
        <button onClick={addHeader1} className={editor.isActive("heading", { level: 1 }) ? "active" : ""}><span>🔠</span> H1</button>
        <button onClick={addHeader2} className={editor.isActive("heading", { level: 2 }) ? "active" : ""}><span>🔤</span> H2</button>
      
        {/* Lists */}
        <button onClick={addBulletList} className={editor.isActive("bulletList") ? "active" : ""}><span>•</span> List</button>
        <button onClick={addOrderedList} className={editor.isActive("orderedList") ? "active" : ""}><span>1.</span> List</button>
      
        {/* Custom Blocks */}
        <button onClick={addPage}>📄 Page</button>
        <button onClick={addCard}><span>🧩</span> Card</button>
        <button onClick={addBanner}><span>📢</span> Banner</button>
        <button onClick={addFAQ}><span>❓</span> FAQ</button>
      
        {/* Table 
        <button onClick={addTable}><span>📊</span> Table</button>
        */}
        <button
          onClick={() => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept = "image/*";
            input.onchange = (e) => {
              const file = e.target.files[0];
              const reader = new FileReader();
              reader.onload = () => {
                editor.chain().focus().insertContent({
                  type: "customBlock",
                  attrs: { variant: "banner", image: reader.result || null },
                  content: [
                    ...(reader ? [{ type: "image", attrs: { src: reader.result } }] : []),
                    { type: "paragraph", content: [{ type: "text", text: "Banner text…" }] }
                  ]
                }).run();
              };
              reader.readAsDataURL(file);
            };
            input.click();
          }}
        >
        
          <span>🖼️</span> Banner
        </button>
        {/* Image Upload 
        <label style={{ display: "flex", alignItems: "center", cursor: "pointer", gap: "6px" }}>
          <span>📁</span> Image
          <input
            type="file"
            accept="image/*"
            onChange={(e) => uploadImage(e.target.files[0])}
            style={{ display: "none" }}
          />
        </label>
      
        <button onClick={insertImage}>
          <span>🌐</span> URL
        </button>
        
        TEXT COLOR 
        <input
          type="color"
          onChange={(e) =>
            editor.chain().focus().setColor(e.target.value).run()
          }
          style={{ width: "35px", height: "28px", padding: 0 }}
        />
        <button onClick={() => editor.chain().focus().unsetColor().run()}>❌ Text Color</button>
         HIGHLIGHT 
        <input
          type="color"
          onChange={(e) =>
            editor.chain().focus().setHighlight({ color: e.target.value }).run()
          }
          style={{ width: "35px", height: "28px", padding: 0 }}
        />
        <button onClick={() => editor.chain().focus().unsetHighlight().run()}>❌ Highlight</button>
        
      */}
      </div>


      {/* Editor Container */}
      <EditorContent editor={editor} className="tiptap-editor" />
    </div>
  );
}
