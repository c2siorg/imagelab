let resizerVertical = document.querySelector('.resizerVertical');
let leftPanel = document.querySelector('.playground-properties-pane');
let rightPanel = document.querySelector('.preview-properties-pane');

let resizeHorizontal = document.querySelector('#resizeHorizontal');
let upperPanel = document.querySelector('.playground-pane');
let lowerPanel = document.querySelector('.information-pane');

resizerVertical.style.cursor = 'col-resize';
resizeHorizontal.style.cursor = 'row-resize';

function makeHorizontallyResizable(resizer, leftPanel, rightPanel) {
    const table = leftPanel.closest('table');
    const minLeftWidth = 100;
    const minRightWidth = 100;
    
    let animationFrameId = null;
    let newLeftWidth = 0;
    
    resizer.addEventListener('mousedown', (e) => {
        e.preventDefault();
        resizerVertical.style.backgroundColor = '#0054a6';
        const initialX = e.clientX;
        const tableRect = table.getBoundingClientRect();
        const tableWidth = tableRect.width;
        const leftInitialWidth = leftPanel.getBoundingClientRect().width;
        const resizerWidth = resizer.offsetWidth;
        
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.right = '0';
        overlay.style.bottom = '0';
        overlay.style.zIndex = '9999';
        overlay.style.cursor = 'col-resize';
        document.body.appendChild(overlay);
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        function onMouseMove(event) {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            
            const dx = event.clientX - initialX;
            newLeftWidth = leftInitialWidth + dx;
            
            if (newLeftWidth < minLeftWidth) {
                newLeftWidth = minLeftWidth;
            }
            if (newLeftWidth > tableWidth - minRightWidth - resizerWidth) {
                newLeftWidth = tableWidth - minRightWidth - resizerWidth;
            }
            
            animationFrameId = requestAnimationFrame(updateLayout);
        }
        
        function updateLayout() {
            const leftPercentage = (newLeftWidth / tableWidth) * 100;
            const rightPercentage = 100 - leftPercentage - (resizerWidth / tableWidth * 100);
            
            leftPanel.style.width = leftPercentage + '%';
            rightPanel.style.width = rightPercentage + '%';
            
            const blocklyDiv = document.getElementById('blocklyDiv');
            if (blocklyDiv) {
                blocklyDiv.style.width = '100%';
            }
        }
        
        function onMouseUp() {
            resizerVertical.style.backgroundColor = '#e8f2fc';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.body.removeChild(overlay);
            
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
                updateLayout();
            }
            
            window.dispatchEvent(new Event('resize'));
        }
    });
}

makeHorizontallyResizable(resizerVertical, leftPanel, rightPanel);

function makeVerticallyResizable(resizer, upperPanel, lowerPanel) {
    const container = upperPanel.parentElement; 
    const minUpperHeight = 200;
    const minLowerHeight = 100;
    
    let animationFrameId = null;
    let newUpperHeight = 0;
    
    resizer.addEventListener('mousedown', (e) => {
        e.preventDefault();
        resizeHorizontal.style.backgroundColor = '#0054a6';
        const initialY = e.clientY;
        const containerRect = container.getBoundingClientRect();
        const containerHeight = containerRect.height;
        const upperInitialHeight = upperPanel.getBoundingClientRect().height;
        const resizerHeight = resizer.offsetHeight;

        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.right = '0';
        overlay.style.bottom = '0';
        overlay.style.zIndex = '9999';
        overlay.style.cursor = 'row-resize';
        document.body.appendChild(overlay);
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        function onMouseMove(event) {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            
            const dy = event.clientY - initialY;
            newUpperHeight = upperInitialHeight + dy;
            
            if (newUpperHeight < minUpperHeight) {
                newUpperHeight = minUpperHeight;
            }
            if (newUpperHeight > containerHeight - minLowerHeight - resizerHeight) {
                newUpperHeight = containerHeight - minLowerHeight - resizerHeight;
            }
            
            animationFrameId = requestAnimationFrame(updateLayout);
        }
        
        function updateLayout() {
            upperPanel.style.height = `${newUpperHeight}px`;
            lowerPanel.style.height = `${containerHeight - newUpperHeight - resizerHeight}px`;

            const blocklyDiv = document.getElementById('blocklyDiv');
            if (blocklyDiv) {
                blocklyDiv.style.height = `${newUpperHeight}px`;
                blocklyDiv.style.maxHeight = `${newUpperHeight}px`;
            }
        }
        
        function onMouseUp() {
            resizeHorizontal.style.backgroundColor = '#e8f2fc';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.body.removeChild(overlay);
            
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
                updateLayout();
            }
            
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
                if (window.Blockly && window.Blockly.svgResize) {
                    const workspace = Blockly.getMainWorkspace();
                    if (workspace) {
                        Blockly.svgResize(workspace);
                    }
                }
            }, 100);
        }
    });
}

makeVerticallyResizable(resizeHorizontal, upperPanel, lowerPanel);
