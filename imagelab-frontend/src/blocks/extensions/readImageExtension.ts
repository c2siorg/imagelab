import * as Blockly from "blockly";
import { usePipelineStore } from "../../store/pipelineStore";

function setFilenameLabel(block: Blockly.Block, value: string) {
  const label = block.getField("filename_label");
  if (label) label.setValue(value);
}

function initReadImageBlock(block: Blockly.Block) {
  // Skip interactive setup in readOnly workspaces (e.g. sidebar previews)
  if (block.workspace.options?.readOnly) return;

  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = "image/*";
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);

  fileInput.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (!file) return;

    const format = file.type.split("/")[1] || "png";
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const base64 = dataUrl.split(",")[1];
      usePipelineStore.getState().setOriginalImage(base64, format);
      setFilenameLabel(block, file.name);
    };
    reader.readAsDataURL(file);

    // Reset so re-selecting the same file triggers change
    fileInput.value = "";
  });

  // Wire the field_image click to open the file picker
  const uploadField = block.getField("upload_button");
  if (uploadField) {
    (uploadField as Blockly.FieldImage).setOnClickHandler(() => {
      fileInput.click();
    });
  }

  const cameraField = block.getField("camera_button");
  if (cameraField) {
    (cameraField as Blockly.FieldImage).setOnClickHandler(() => {
      usePipelineStore.getState().openCameraModal(({ image, format, label }) => {
        if (!block.workspace) {
          return;
        }

        usePipelineStore.getState().setOriginalImage(image, format);
        setFilenameLabel(block, label);
      });
    });
  }

  // Register a reset callback when the image is cleared
  usePipelineStore.getState().registerImageReset(() => {
    setFilenameLabel(block, "No image");
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
