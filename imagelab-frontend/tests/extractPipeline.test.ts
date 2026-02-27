import { describe, expect, it } from 'vitest';
import type { WorkspaceSvg } from 'blockly';
import { extractPipeline } from '../src/hooks/usePipeline';
import { block, field, input, INPUT_TYPE_VALUE, workspace } from './blocklyMockFactory';

// helper to avoid repeating the cast everywhere
function asWs(ws: unknown): WorkspaceSvg {
  return ws as WorkspaceSvg;
}

describe('extractPipeline', () => {
  it('returns [] when there are no blocks at all', () => {
    expect(extractPipeline(asWs(workspace([])))).toEqual([]);
  });

  it('returns [] if basic_readimage is not in the workspace', () => {
    // pipeline can only start from a reader block
    expect(extractPipeline(asWs(workspace([block('filtering_bilateral')])))).toEqual([]);
  });

  it('handles a standalone reader block with a filename param', () => {
    const read = block('basic_readimage', [input([field('filename_label', 'cat.png')])]);
    const pipeline = extractPipeline(asWs(workspace([read])));
    expect(pipeline).toHaveLength(1);
    expect(pipeline[0].type).toBe('basic_readimage');
    expect(pipeline[0].params).toMatchObject({ filename_label: 'cat.png' });
  });

  it('walks the chain in order: first block should come first', () => {
    const sharpen = block('filtering_sharpen', [input([field('strength', 1.2)])]);
    const morph = block('filtering_morphological', [input([field('type', 'TOPHAT')])], sharpen);
    const reader = block('basic_readimage', [input([field('filename_label', 'x.png')])], morph);
    const pipeline = extractPipeline(asWs(workspace([reader])));
    expect(pipeline.map((s) => s.type)).toEqual([
      'basic_readimage',
      'filtering_morphological',
      'filtering_sharpen',
    ]);
    expect(pipeline[1].params).toMatchObject({ type: 'TOPHAT' }); // dropdown field check
  });

  it('picks up numeric and color field values from a drawing block', () => {
    const drawLine = block('drawingoperations_drawline', [
      input([field('thickness', 2), field('rgbcolors_input', '#ff00ff')]),
    ]);
    const reader = block('basic_readimage', [input([field('filename_label', 'x.png')])], drawLine);
    const pipeline = extractPipeline(asWs(workspace([reader])));
    expect(pipeline[1].params).toMatchObject({ thickness: 2, rgbcolors_input: '#ff00ff' });
  });

  it('pulls params from VALUE-connected blocks', () => {
    const borderEachSide = block('border_each_side', [
      input([field('borderTop', 3), field('borderLeft', 4), field('borderRight', 5), field('borderBottom', 6)]),
    ]);
    const applyBorders = block('thresholding_applyborders', [
      input([], { type: INPUT_TYPE_VALUE, connected: borderEachSide }),
    ]);
    const read = block('basic_readimage', [input([field('filename_label', 'x.png')])], applyBorders);
    const pipeline = extractPipeline(asWs(workspace([read])));
    expect(pipeline.map((s) => s.type)).toEqual(['basic_readimage', 'thresholding_applyborders']);
    expect(pipeline[1].params).toMatchObject({ borderTop: 3, borderLeft: 4, borderRight: 5, borderBottom: 6 });
  });

  it('ignores connected blocks when the input type is not VALUE (type 1)', () => {
    // type: 2 is a statement input, should not be followed
    const child = block('border_for_all', [input([field('border_all_sides', 9)])]);
    const parent = block('some_parent', [input([], { type: 2, connected: child })]);
    const read = block('basic_readimage', [input([field('filename_label', 'x.png')])], parent);
    const pipeline = extractPipeline(asWs(workspace([read])));
    expect(pipeline[1].params).toEqual({});
  });
});
