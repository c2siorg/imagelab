// Path the app serves Blockly's media from (sprites.png for the zoom and trash
// controls, and the click/delete sounds). vite.config.ts serves and bundles the
// files from the installed blockly package at this path; keep the two in sync.
export const BLOCKLY_MEDIA_PATH = "blockly-media";

/** The `media` option for Blockly.inject. */
export const BLOCKLY_MEDIA_URL = `${import.meta.env.BASE_URL}${BLOCKLY_MEDIA_PATH}/`;
