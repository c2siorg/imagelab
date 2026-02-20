import { useEffect, useState } from 'react';
import * as Blockly from 'blockly';
import { categories } from '../blocks/categories';
import { imagelabTheme } from '../blocks/theme';

export interface BlockPreview {
  svgDataUrl: string;
  svgMarkup: string;
  width: number;
  height: number;
}

/**
 * Fixed scale applied to all block previews so text renders at a uniform size.
 * Theme font is 11px; scale 0.75 → ~8px display text — readable and consistent.
 */
const PREVIEW_SCALE = 0.75;

function generatePreviews(): Map<string, BlockPreview> {
  const container = document.createElement('div');
  container.style.position = 'absolute';
  container.style.left = '-9999px';
  container.style.top = '-9999px';
  container.style.width = '800px';
  container.style.height = '600px';
  document.body.appendChild(container);

  const ws = Blockly.inject(container, {
    readOnly: true,
    renderer: 'zelos',
    theme: imagelabTheme,
    scrollbars: false,
  });

  const map = new Map<string, BlockPreview>();

  for (const category of categories) {
    for (const blockInfo of category.blocks) {
      try {
        const block = ws.newBlock(blockInfo.type);
        block.initSvg();
        block.render();

        const svgRoot = block.getSvgRoot();
        if (!svgRoot) continue;

        const bbox = svgRoot.getBBox();
        const padding = 4;
        const naturalWidth = Math.ceil(bbox.width + padding * 2);
        const naturalHeight = Math.ceil(bbox.height + padding * 2);
        const clone = svgRoot.cloneNode(true) as SVGElement;

        const width = Math.ceil(naturalWidth * PREVIEW_SCALE);
        const height = Math.ceil(naturalHeight * PREVIEW_SCALE);

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        svg.setAttribute('width', String(width));
        svg.setAttribute('height', String(height));
        svg.setAttribute(
          'viewBox',
          `${bbox.x - padding} ${bbox.y - padding} ${naturalWidth} ${naturalHeight}`,
        );

        const workspaceSvg = ws.getParentSvg();
        const defs = workspaceSvg.querySelector('defs');
        if (defs) {
          svg.appendChild(defs.cloneNode(true));
        }

        svg.appendChild(clone);

        const serializer = new XMLSerializer();
        const svgStr = serializer.serializeToString(svg);
        const dataUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgStr)}`;

        map.set(blockInfo.type, { svgDataUrl: dataUrl, svgMarkup: svgStr, width, height });
      } catch {
        // skip blocks that fail to render
      }
    }
  }

  ws.dispose();
  container.remove();

  return map;
}

export function useBlockPreviews(): Map<string, BlockPreview> {
  const [previews, setPreviews] = useState<Map<string, BlockPreview>>(new Map());

  useEffect(() => {
    // Defer to next frame so the main workspace renders first
    const frameId = requestAnimationFrame(() => {
      setPreviews(generatePreviews());
    });
    return () => cancelAnimationFrame(frameId);
  }, []);

  return previews;
}
