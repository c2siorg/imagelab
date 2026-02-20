export const drawingBlocks = [
  {
    type: "drawingoperations_drawline",
    message0: "Draw a line %1 with thickness of %2 %3 , color %4 starting point x %5 , y %6 %7 ending point x %8 , y %9",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1 },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#2828cc" },
      { type: "field_number", name: "starting_point_x1", value: 0 },
      { type: "field_number", name: "starting_point_y1", value: 0 },
      { type: "input_dummy" },
      { type: "field_number", name: "ending_point_x", value: 0 },
      { type: "field_number", name: "ending_point_y", value: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "drawing_style",
    tooltip: "Draws a line on the image"
  },
  {
    type: "drawingoperations_drawcircle",
    message0: "Draw a circle %1 with thickness of %2 , %3 radius of %4 %5 color %6 center point x %7 and y %8",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "radius", value: 5, min: 1 },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#2828cc" },
      { type: "field_number", name: "center_point_x", value: 0 },
      { type: "field_number", name: "center_point_y", value: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "drawing_style",
    tooltip: "Draws a circle on the image"
  },
  {
    type: "drawingoperations_drawellipse",
    message0: "Draw an ellipse with thickness of %1 %2 , height %3 , width %4 , rotate by %5 %6 color %7 center point x %8 and y %9",
    args0: [
      { type: "field_number", name: "thickness", value: 2, min: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "height", value: 0, min: 0 },
      { type: "field_number", name: "width", value: 0, min: 0 },
      { type: "field_angle", name: "angle", angle: 90 },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#2828cc" },
      { type: "field_number", name: "center_point_x", value: 0 },
      { type: "field_number", name: "center_point_y", value: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "drawing_style",
    tooltip: "Draws an ellipse on the image"
  },
  {
    type: "drawingoperations_drawrectangle",
    message0: "Draw a rectangle %1 with thickness of %2 %3 , color %4 , starting point x %5 and y %6 , ending point x %7 and y %8",
    args0: [
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1 },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#2828cc" },
      { type: "field_number", name: "starting_point_x", value: 0 },
      { type: "field_number", name: "starting_point_y", value: 0 },
      { type: "field_number", name: "ending_point_x", value: 0 },
      { type: "field_number", name: "ending_point_y", value: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "drawing_style",
    tooltip: "Draws a rectangle on the image"
  },
  {
    type: "drawingoperations_drawarrowline",
    message0: "Draw an arrow line %1 with color %2 with thickness %3 from starting point x %4 and y %5 to ending point x %6 and y %7",
    args0: [
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#2828cc" },
      { type: "field_number", name: "thickness", value: 2, min: 1 },
      { type: "field_number", name: "starting_point_x", value: 0 },
      { type: "field_number", name: "starting_point_y", value: 0 },
      { type: "field_number", name: "ending_point_x", value: 0 },
      { type: "field_number", name: "ending_point_y", value: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "drawing_style",
    tooltip: "Draws an arrow line on the image"
  },
  {
    type: "drawingoperations_drawtext",
    message0: "Draw text %1 %2 with thickness of %3 %4 , by scale of %5 %6 , color %7 at point x %8 and y %9",
    args0: [
      { type: "field_input", name: "draw_text", text: "Image Lab" },
      { type: "input_dummy" },
      { type: "field_number", name: "thickness", value: 2, min: 1 },
      { type: "input_dummy" },
      { type: "field_number", name: "scale", value: 1, min: 1 },
      { type: "input_dummy" },
      { type: "field_colour", name: "rgbcolors_input", colour: "#2828cc" },
      { type: "field_number", name: "starting_point_x", value: 0 },
      { type: "field_number", name: "starting_point_y", value: 0 }
    ],
    previousStatement: null,
    nextStatement: null,
    style: "drawing_style",
    tooltip: "Draws text on the image"
  }
];
