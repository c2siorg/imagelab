import * as Blockly from "blockly";
import { usePipelineStore } from "../../store/pipelineStore";
import { loadImageFile } from "../../hooks/useImageUpload";

function initReadImageBlock(block: Blockly.Block) {
  if (block.workspace.options?.readOnly) return;

  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (!file) return;

    loadImageFile(file).then(() => {
      const label = block.getField("filename_label");
      if (label) label.setValue(file.name);
    });

    fileInput.value = "";
  });

  const uploadField = block.getField("upload_button");
  if (uploadField) {
    (uploadField as Blockly.FieldImage).setOnClickHandler(() => {
      fileInput.click();
    });
  }

  usePipelineStore.getState().registerImageReset(() => {
    const label = block.getField("filename_label");
    if (label) label.setValue("No image");
  });

  // Clean up on block disposal (deletion or workspace clear)
  block.dispose = new Proxy(block.dispose, {
    apply(target, thisArg, args) {
      fileInput.remove();
      // Clear image from store when read_image block is deleted
      usePipelineStore.getState().clearImage();
      return Reflect.apply(target, thisArg, args);
    },
  });
}

export function registerReadImageExtension() {
  Blockly.Extensions.register("read_image_upload", function (this: Blockly.Block) {
    initReadImageBlock(this);
  });
}
