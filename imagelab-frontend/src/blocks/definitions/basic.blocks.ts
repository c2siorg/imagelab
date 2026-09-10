/* 20×20 upload-cloud icon (Lucide-style) as an inline SVG data URI */
const UPLOAD_ICON =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/%3E%3Cpolyline points='17 8 12 3 7 8'/%3E%3Cline x1='12' y1='3' x2='12' y2='15'/%3E%3C/svg%3E";
const CAMERA_ICON =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3Z'/%3E%3Ccircle cx='12' cy='13' r='3'/%3E%3C/svg%3E";

export const basicBlocks = [
  {
    type: "basic_readimage",
    message0: "Read image %1 %2 %3",
    args0: [
      {
        type: "field_label_serializable",
        name: "filename_label",
        text: "No image",
      },
      {
        type: "field_image",
        name: "upload_button",
        src: UPLOAD_ICON,
        width: 20,
        height: 20,
        alt: "Upload image",
      },
      {
        type: "field_image",
        name: "camera_button",
        src: CAMERA_ICON,
        width: 20,
        height: 20,
        alt: "Capture image",
      },
    ],
    nextStatement: null,
    style: "basic_style",
    tooltip:
      "Click the upload icon to load an image - Allows you to upload an image file from your device. Supported formats include JPEG, PNG, and GIF. Once uploaded, the image will be available for processing in subsequent blocks.",
    extensions: ["read_image_upload"],
  },
  {
    type: "basic_writeimage",
    message0: "Write image",
    previousStatement: null,
    style: "basic_style",
    tooltip:
      "Output the processed image - Displays the final processed image as output. Place this block at the end of your pipeline to see the result of all applied operations.",
  },
];
