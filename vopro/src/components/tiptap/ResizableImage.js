// src/tiptap/ResizableImage.js
import Image from "@tiptap/extension-image";

export const ResizableImage = Image.extend({
  
  addAttributes() {
    return {
      ...this.parent?.(),
      width: { default: "100%" },
      height: { default: "auto" },
      x: { default: 0 }, // horizontal offset in px
      y: { default: 0 }, // vertical offset in px
    };
  },

  addNodeView() {
    return ({ node, updateAttributes }) => {
      // wrapper
      const wrapper = document.createElement("div");
      wrapper.style.position = "relative";
      wrapper.style.display = "inline-block";
      wrapper.style.touchAction = "none"; // allow pointer drag

      // image element
      const img = document.createElement("img");
      img.src = node.attrs.src;
      img.style.width = node.attrs.width || "100%";
      img.style.height = node.attrs.height || "auto";
      img.style.maxWidth = "100%";
      img.style.borderRadius = "6px";
      img.style.userSelect = "none";
      img.style.display = "block";
      // apply saved offsets (translate)
      wrapper.style.transform = `translate(${node.attrs.x || 0}px, ${node.attrs.y || 0}px)`;

      // resize handle
      const handle = document.createElement("div");
      handle.style.width = "14px";
      handle.style.height = "14px";
      handle.style.background = "#1d4ed8";
      handle.style.position = "absolute";
      handle.style.right = "-8px";
      handle.style.bottom = "-8px";
      handle.style.cursor = "nwse-resize";
      handle.style.borderRadius = "3px";
      handle.style.zIndex = "20";

      // dragging state for move
      let dragging = false;
      let startX = 0;
      let startY = 0;
      let startImgX = 0;
      let startImgY = 0;

      // pointerdown on image => begin reposition (unless user clicked handle)
      img.addEventListener("pointerdown", (e) => {
        // ignore right-click or ctrl/alt+click if you want
        if (e.button !== 0) return;
        // if clicking handle, skip here (handle has its own mousedown)
        if (e.target === handle) return;

        e.preventDefault();
        dragging = true;
        wrapper.setPointerCapture(e.pointerId);
        startX = e.clientX;
        startY = e.clientY;
        startImgX = parseInt(node.attrs.x || 0, 10);
        startImgY = parseInt(node.attrs.y || 0, 10);

        const onMove = (ev) => {
          if (!dragging) return;
          const dx = ev.clientX - startX;
          const dy = ev.clientY - startY;
          const nx = startImgX + dx;
          const ny = startImgY + dy;
          wrapper.style.transform = `translate(${nx}px, ${ny}px)`;
          // update attributes live so dragging is smooth and saved on drop
          updateAttributes({ ...node.attrs, x: nx, y: ny });
        };

        const onUp = () => {
          dragging = false;
          wrapper.releasePointerCapture(e.pointerId);
          window.removeEventListener("pointermove", onMove);
          window.removeEventListener("pointerup", onUp);
        };

        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
      });

      // Resize handle logic (mouse drag)
      handle.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        e.stopPropagation(); // don't start move
        const startClientX = e.clientX;
        const startWidth = img.offsetWidth;
        let moving = true;

        const onMove = (ev) => {
          if (!moving) return;
          const dx = ev.clientX - startClientX;
          const newWidth = Math.max(40, startWidth + dx);
          img.style.width = newWidth + "px";
          updateAttributes({ ...node.attrs, width: newWidth + "px", height: "auto" });
        };

        const onUp = () => {
          moving = false;
          window.removeEventListener("pointermove", onMove);
          window.removeEventListener("pointerup", onUp);
        };

        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
      });

      // Add elements
      wrapper.appendChild(img);
      wrapper.appendChild(handle);

      // Make wrapper keyboard accessible for selection (optional)
      wrapper.setAttribute("tabindex", "-1");

      // return node view
      return {
        dom: wrapper,
        // update helps when React / editor asks to re-render node view
        update: (updatedNode) => {
          // if src changed, update img
          if (updatedNode.attrs.src !== img.src) {
            img.src = updatedNode.attrs.src;
          }
          // update dims & transform
          img.style.width = updatedNode.attrs.width || img.style.width || "100%";
          img.style.height = updatedNode.attrs.height || img.style.height || "auto";
          img.style.transform = `translate(${updatedNode.attrs.x || 0}px, ${updatedNode.attrs.y || 0}px)`;
          return true;
        },
      };
    };
  },
});
