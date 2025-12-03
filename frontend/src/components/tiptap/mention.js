import { Suggestion } from "@tiptap/suggestion";

export const mentionConfig = {
  char: "@",
  items: ({ query }) => {
    const list = [
      { id: "assistant", label: "AI Assistant" },
      { id: "support", label: "Support Bot" },
    ];
    return list.filter(item =>
      item.label.toLowerCase().includes(query.toLowerCase())
    );
  },
  render: () => {
    let popup;
    return {
      onStart: props => {
        popup = document.createElement("div");
        popup.className = "mention-popup";
        popup.innerHTML = props.items
          .map(i => `<div class="mention-item">${i.label}</div>`)
          .join("");
        document.body.appendChild(popup);
        props.clientRect && applyPopupPosition(popup, props.clientRect());
      },
      onUpdate(props) {
        popup.innerHTML = props.items
          .map(i => `<div class="mention-item">${i.label}</div>`)
          .join("");
        props.clientRect && applyPopupPosition(popup, props.clientRect());
      },
      onExit() {
        popup.remove();
      },
    };
  },
};

function applyPopupPosition(popup, rect) {
  popup.style.position = "absolute";
  popup.style.top = `${rect.bottom + window.scrollY}px`;
  popup.style.left = `${rect.left + window.scrollX}px`;
}
