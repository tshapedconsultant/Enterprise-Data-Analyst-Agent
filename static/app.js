// API Configuration
const API_BASE_URL = window.location.origin;

// DOM Elements
const queryInput = document.getElementById('queryInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const resultsSection = document.getElementById('resultsSection');
const resultsContent = document.getElementById('resultsContent');
const emptyState = document.getElementById('emptyState');
const exampleChips = document.querySelectorAll('.example-chip');

// State
let isAnalyzing = false;

// Event Listeners
analyzeBtn.addEventListener('click', handleAnalyze);
clearBtn.addEventListener('click', handleClear);
queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        handleAnalyze();
    }
});

// Example chip clicks
exampleChips.forEach(chip => {
    chip.addEventListener('click', () => {
        const query = chip.getAttribute('data-query');
        queryInput.value = query;
        queryInput.focus();
    });
});

// Main analyze function
async function handleAnalyze() {
    const query = queryInput.value.trim();
    
    if (!query) {
        showError('Please enter a question or request');
        return;
    }

    if (isAnalyzing) {
        return;
    }

    // Update UI
    setAnalyzing(true);
    hideEmptyState();
    clearResults();
    
    try {
        const response = await fetch(`${API_BASE_URL}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                max_iterations: 10,
                message_window: 8
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        // Read streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                try {
                    const event = JSON.parse(line);
                    displayEvent(event);
                } catch (e) {
                    console.error('Failed to parse event:', e);
                }
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError(`Failed to analyze: ${error.message}`);
    } finally {
        setAnalyzing(false);
    }
}

// Display an event from the stream
function displayEvent(event) {
    const { type, agent, decision, reasoning, output, error, data } = event;
    
    let itemClass = 'result-item';
    let icon = '📊';
    let typeLabel = 'Event';
    let content = '';
    
    switch (type) {
        case 'start':
            itemClass += ' decision';
            icon = '🚀';
            typeLabel = 'Started';
            content = data || 'Analysis started';
            break;
            
        case 'decision':
            itemClass += ' decision';
            icon = '🎯';
            typeLabel = 'Decision';
            content = `Routing to: ${decision || 'Unknown'}`;
            if (reasoning) {
                content += `\n\nReasoning: ${reasoning}`;
            }
            break;
            
        case 'action':
            itemClass += ' action';
            icon = '⚙️';
            typeLabel = agent || 'Action';
            content = output || 'Processing...';
            break;
            
        case 'finish':
            itemClass += ' finish';
            icon = '✅';
            typeLabel = 'Complete';
            content = data || 'Analysis completed successfully';
            break;
            
        case 'error':
            itemClass += ' error';
            icon = '❌';
            typeLabel = 'Error';
            content = error || 'An error occurred';
            break;
            
        default:
            content = JSON.stringify(event, null, 2);
    }
    
    const item = document.createElement('div');
    item.className = itemClass;
    item.innerHTML = `
        <div class="result-header">
            <span class="result-icon">${icon}</span>
            <span class="result-type">${typeLabel}</span>
        </div>
        <div class="result-content">${escapeHtml(content)}</div>
    `;
    
    resultsContent.appendChild(item);
    resultsSection.style.display = 'block';
    
    // Check if this is a strategy from Business_Strategist and render it nicely
    if (type === 'action' && agent === 'Business_Strategist' && output) {
        let strategy = null;
        
        // Try to find STRATEGY: in output
        if (output.includes('STRATEGY:')) {
            try {
                // Extract JSON from STRATEGY: prefix
                const jsonStart = output.indexOf('STRATEGY:') + 'STRATEGY:'.length;
                let jsonStr = output.substring(jsonStart).trim();
                
                // Remove markdown code blocks if present
                jsonStr = jsonStr.replace(/^```json\s*/, '').replace(/^```\s*/, '').replace(/\s*```$/, '');
                
                // Handle double curly braces (from template escaping) - convert {{ to { and }} to }
                // Do this multiple times in case of nested escaping
                let prevJsonStr = '';
                while (jsonStr !== prevJsonStr) {
                    prevJsonStr = jsonStr;
                    jsonStr = jsonStr.replace(/\{\{/g, '{').replace(/\}\}/g, '}');
                }
                
                // Also handle any remaining escaped braces
                jsonStr = jsonStr.replace(/\{\s*\{/g, '{').replace(/\}\s*\}/g, '}');
                
                // Clean up any leading/trailing whitespace or newlines
                jsonStr = jsonStr.trim();
                
                // Remove any leading/trailing braces that might be duplicated
                if (jsonStr.startsWith('{{')) jsonStr = jsonStr.substring(1);
                if (jsonStr.endsWith('}}')) jsonStr = jsonStr.substring(0, jsonStr.length - 1);
                
                strategy = JSON.parse(jsonStr);
                console.log('Parsed strategy:', strategy);
            } catch (e) {
                console.error('Failed to parse strategy:', e, 'Output:', output);
                // Try one more time with aggressive cleanup
                try {
                    let jsonStr = output.substring(output.indexOf('STRATEGY:') + 'STRATEGY:'.length).trim();
                    jsonStr = jsonStr.replace(/^```json\s*/, '').replace(/^```\s*/, '').replace(/\s*```$/, '');
                    // More aggressive: replace all {{ with { and }} with }
                    jsonStr = jsonStr.split('{{').join('{').split('}}').join('}');
                    jsonStr = jsonStr.trim();
                    strategy = JSON.parse(jsonStr);
                    console.log('Parsed strategy with aggressive cleanup:', strategy);
                } catch (e2) {
                    console.error('Failed to parse even with aggressive cleanup:', e2);
                }
            }
        }
        
        // Also check if output contains JSON directly (might be wrapped in text)
        if (!strategy && output.includes('"actions"') && output.includes('"rating"')) {
            try {
                // Try to extract JSON object from the output - handle both single and double braces
                const jsonMatch = output.match(/(?:\{\{|\{)[\s\S]*"actions"[\s\S]*?(?:\}\}|\})/);
                if (jsonMatch) {
                    let jsonStr = jsonMatch[0];
                    // Remove markdown code blocks if present
                    jsonStr = jsonStr.replace(/^```json\s*/, '').replace(/^```\s*/, '').replace(/\s*```$/, '');
                    // Handle double curly braces
                    jsonStr = jsonStr.replace(/\{\{/g, '{').replace(/\}\}/g, '}');
                    jsonStr = jsonStr.trim();
                    strategy = JSON.parse(jsonStr);
                    console.log('Parsed strategy from JSON match:', strategy);
                }
            } catch (e) {
                console.error('Failed to parse JSON from output:', e);
            }
        }
        
        if (strategy && strategy.actions) {
            // Render strategy recommendations nicely
            renderStrategy(strategy, item);
        }
    }
    
    // Scroll to bottom
    resultsContent.scrollTop = resultsContent.scrollHeight;
}

// UI Helper Functions
function setAnalyzing(analyzing) {
    isAnalyzing = analyzing;
    analyzeBtn.disabled = analyzing;
    
    const buttonText = analyzeBtn.querySelector('.button-text');
    const buttonLoader = analyzeBtn.querySelector('.button-loader');
    
    if (analyzing) {
        buttonText.style.display = 'none';
        buttonLoader.style.display = 'flex';
    } else {
        buttonText.style.display = 'inline';
        buttonLoader.style.display = 'none';
    }
}

function clearResults() {
    resultsContent.innerHTML = '';
    resultsSection.style.display = 'none';
}

function hideEmptyState() {
    emptyState.style.display = 'none';
}

function showEmptyState() {
    emptyState.style.display = 'block';
}

function handleClear() {
    clearResults();
    queryInput.value = '';
    queryInput.focus();
    showEmptyState();
}

function showError(message) {
    const errorEvent = {
        type: 'error',
        error: message
    };
    displayEvent(errorEvent);
    setAnalyzing(false);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Strategy rendering function
function renderStrategy(strategy, parentItem) {
    const contentDiv = parentItem.querySelector('.result-content');
    if (!contentDiv) return;
    
    // Sort actions by rating (highest first)
    const sortedActions = [...strategy.actions].sort((a, b) => (b.rating || 0) - (a.rating || 0));
    
    let strategyHTML = '';
    
    // Add summary if available
    if (strategy.summary) {
        strategyHTML += `<div class="strategy-summary" style="margin-bottom: 20px; padding: 15px; background: #f0f7ff; border-left: 4px solid #003366; border-radius: 4px;">
            <strong>Strategic Insight:</strong> ${escapeHtml(strategy.summary)}
        </div>`;
    }
    
    // Add actions
    strategyHTML += '<div class="strategy-actions" style="display: flex; flex-direction: column; gap: 15px;">';
    
    sortedActions.forEach((action, index) => {
        const rating = action.rating || 0;
        const ratingColor = rating >= 8 ? '#00CC66' : rating >= 6 ? '#FF9900' : '#CC0000';
        const ratingLabel = rating >= 8 ? 'High Priority' : rating >= 6 ? 'Medium Priority' : 'Low Priority';
        
        strategyHTML += `
            <div class="strategy-action" style="padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid ${ratingColor};">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; font-size: 16px; color: #003366; margin-bottom: 8px;">
                            Action ${index + 1}: ${escapeHtml(action.action)}
                        </div>
                        ${action.rationale ? `<div style="color: #666; font-size: 14px; line-height: 1.5;">${escapeHtml(action.rationale)}</div>` : ''}
                    </div>
                    <div style="margin-left: 15px; text-align: center; min-width: 80px;">
                        <div style="font-size: 32px; font-weight: bold; color: ${ratingColor}; line-height: 1;">
                            ${rating}
                        </div>
                        <div style="font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">
                            ${ratingLabel}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    strategyHTML += '</div>';
    
    // Update content
    contentDiv.innerHTML = strategyHTML;
}

// Auto-resize textarea
queryInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});

