document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');
    const tooltip = document.getElementById('tooltip');
    
    // Set canvas dimensions to match the window
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    // Resize canvas when window is resized
    window.addEventListener('resize', function() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
    
    // Node class
    class Node {
        constructor(x, y, radius, speedX, speedY, thought) {
            this.x = x;
            this.y = y;
            this.radius = radius;
            this.color = 'rgba(255, 255, 255, 0.8)';
            this.glowColor = 'rgba(255, 255, 255, 0.3)';
            this.speedX = speedX;
            this.speedY = speedY;
            this.thought = thought;
            this.originalRadius = radius;
            this.connections = [];
            this.pulsePhase = Math.random() * Math.PI * 2; // Random phase for pulsing
            this.pulseSpeed = 0.03 + Math.random() * 0.04; // Random pulse speed
            this.blinkTimer = 0;
            this.blinkInterval = 50 + Math.floor(Math.random() * 200); // Random blink interval
            this.isBlinking = false;
            this.blinkDuration = 5 + Math.floor(Math.random() * 10);
        }
        
        update() {
            // Move node
            this.x += this.speedX;
            this.y += this.speedY;
            
            // Boundary check
            if (this.x <= this.radius || this.x >= canvas.width - this.radius) {
                this.speedX = -this.speedX;
            }
            if (this.y <= this.radius || this.y >= canvas.height - this.radius) {
                this.speedY = -this.speedY;
            }
            
            // Pulse effect
            this.pulsePhase += this.pulseSpeed;
            let pulseFactor = Math.sin(this.pulsePhase) * 0.2 + 1;
            this.radius = this.originalRadius * pulseFactor;
            
            // Blink effect
            this.blinkTimer++;
            if (this.blinkTimer >= this.blinkInterval) {
                this.isBlinking = true;
                this.blinkDuration--;
                
                if (this.blinkDuration <= 0) {
                    this.isBlinking = false;
                    this.blinkTimer = 0;
                    this.blinkDuration = 5 + Math.floor(Math.random() * 10);
                    this.blinkInterval = 50 + Math.floor(Math.random() * 200);
                }
            }
        }
        
        draw() {
            // Set node brightness based on blinking
            let nodeOpacity = this.isBlinking ? 1 : 0.8;
            let glowOpacity = this.isBlinking ? 0.6 : 0.3;
            
            this.color = `rgba(255, 255, 255, ${nodeOpacity})`;
            this.glowColor = `rgba(255, 255, 255, ${glowOpacity})`;
            
            // Draw glow
            const gradient = ctx.createRadialGradient(
                this.x, this.y, this.radius * 0.5,
                this.x, this.y, this.radius * 2.5
            );
            gradient.addColorStop(0, this.glowColor);
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
            
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius * 2, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // Draw node
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();
        }
        
        drawConnections() {
            for (const connectedNode of this.connections) {
                // Calculate distance for opacity
                const dx = this.x - connectedNode.x;
                const dy = this.y - connectedNode.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // Only draw if within certain distance
                if (distance < 300) {
                    // Calculate opacity based on distance and if node is blinking
                    let baseOpacity = 1 - distance / 300;
                    if (this.isBlinking || connectedNode.isBlinking) {
                        baseOpacity *= 1.5;
                    }
                    baseOpacity = Math.min(baseOpacity, 0.8); // Cap at 0.8
                    
                    // Draw connection line
                    ctx.beginPath();
                    ctx.moveTo(this.x, this.y);
                    ctx.lineTo(connectedNode.x, connectedNode.y);
                    ctx.strokeStyle = `rgba(255, 255, 255, ${baseOpacity * 0.6})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
        
        isMouseOver(mouseX, mouseY) {
            const dx = this.x - mouseX;
            const dy = this.y - mouseY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            return distance <= this.radius * 2;
        }
    }
    
    // Thoughts for nodes
    const thoughts = [
        "Insight connects memories",
        "Pattern recognition enhances learning",
        "Visual cues improve recall",
        "Cross-referencing strengthens knowledge",
        "Association builds neural pathways",
        "Gamification increases engagement",
        "Spaced repetition optimizes memory",
        "Linked concepts create understanding",
        "Knowledge graphs expand thinking",
        "Cognitive maps enhance creativity",
        "Neural networks mirror thoughts",
        "Synapse formation requires connection",
        "Mindfulness improves focus",
        "Deep work produces insights",
        "Contextual learning is powerful"
    ];
    
    // Create nodes
    const nodes = [];
    const nodeCount = Math.min(50, window.innerWidth / 40);
    
    for (let i = 0; i < nodeCount; i++) {
        const x = Math.random() * canvas.width;
        const y = Math.random() * canvas.height;
        const radius = 12 + Math.random() * 14; // Between 6 and 10
        const speedX = (Math.random() - 0.5) * 0.3;
        const speedY = (Math.random() - 0.5) * 0.3;
        const thought = thoughts[Math.floor(Math.random() * thoughts.length)];
        
        nodes.push(new Node(x, y, radius, speedX, speedY, thought));
    }
    
    // Connect nodes
    for (const node of nodes) {
        // Connect to 2-4 other random nodes
        const connectionCount = 2 + Math.floor(Math.random() * 3);
        const shuffledNodes = [...nodes].sort(() => 0.5 - Math.random());
        
        for (let i = 0; i < connectionCount && i < shuffledNodes.length; i++) {
            if (node !== shuffledNodes[i]) {
                node.connections.push(shuffledNodes[i]);
            }
        }
    }
    
    // Mouse tracking
    let mouseX = null;
    let mouseY = null;
    let hoveredNode = null;
    
    canvas.addEventListener('mousemove', function(e) {
        const rect = canvas.getBoundingClientRect();
        mouseX = e.clientX - rect.left;
        mouseY = e.clientY - rect.top;
        
        // Check for node hover
        hoveredNode = null;
        for (const node of nodes) {
            if (node.isMouseOver(mouseX, mouseY)) {
                hoveredNode = node;
                break;
            }
        }
        
        // Show/hide tooltip
        if (hoveredNode) {
            tooltip.style.opacity = '1';
            tooltip.style.left = (e.clientX + 10) + 'px';
            tooltip.style.top = (e.clientY + 10) + 'px';
            tooltip.textContent = hoveredNode.thought;
        } else {
            tooltip.style.opacity = '0';
        }
    });
    
    canvas.addEventListener('mouseout', function() {
        mouseX = null;
        mouseY = null;
        hoveredNode = null;
        tooltip.style.opacity = '0';
    });
    
    // Animation loop
    function animate() {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw connections first
        for (const node of nodes) {
            node.drawConnections();
        }
        
        // Update and draw nodes
        for (const node of nodes) {
            node.update();
            node.draw();
            
            // Highlight hovered node
            if (node === hoveredNode) {
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.radius * 2.5, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    // Start animation
    animate();
    
    // Simulated countdown timer
    // This would be replaced with actual countdown logic in a real implementation
    function updateCountdown() {
        // In a real implementation, this would calculate time remaining until launch
        // For now, just decrease the countdown each minute
        
        setTimeout(updateCountdown, 60000); // Update every minute
    }
    
    // Start countdown
    updateCountdown();
});