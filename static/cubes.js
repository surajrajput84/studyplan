// Cubes Background Animation
// Vanilla JS version adapted from React Bits component

class CubesBackground {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      gridSize: options.gridSize || 8,
      maxAngle: options.maxAngle || 60,
      radius: options.radius || 4,
      easing: options.easing || 'power3.out',
      enterDuration: options.enterDuration || 0.3,
      leaveDuration: options.leaveDuration || 0.6,
      borderStyle: options.borderStyle || '2px dashed rgba(82, 39, 255, 0.3)',
      faceColor: options.faceColor || 'rgba(26, 26, 46, 0.6)',
      rippleColor: options.rippleColor || '#ff6b6b',
      rippleSpeed: options.rippleSpeed || 1.5,
      autoAnimate: options.autoAnimate !== false,
      rippleOnClick: options.rippleOnClick !== false
    };

    this.sceneRef = null;
    this.rafRef = null;
    this.idleTimer = null;
    this.userActive = false;
    this.simPos = { x: 0, y: 0 };
    this.simTarget = { x: 0, y: 0 };
    this.simRAF = null;

    this.init();
  }

  init() {
    this.createScene();
    this.bindEvents();
    if (this.options.autoAnimate) {
      this.startAutoAnimation();
    }
  }

  createScene() {
    const wrapper = document.createElement('div');
    wrapper.className = 'cubes-wrapper';
    
    const scene = document.createElement('div');
    scene.className = 'cubes-scene';
    scene.style.gridTemplateColumns = `repeat(${this.options.gridSize}, 1fr)`;
    scene.style.gridTemplateRows = `repeat(${this.options.gridSize}, 1fr)`;
    
    // Set CSS variables
    this.container.style.setProperty('--cube-face-border', this.options.borderStyle);
    this.container.style.setProperty('--cube-face-bg', this.options.faceColor);

    // Create cubes
    for (let r = 0; r < this.options.gridSize; r++) {
      for (let c = 0; c < this.options.gridSize; c++) {
        const cube = document.createElement('div');
        cube.className = 'cube';
        cube.dataset.row = r;
        cube.dataset.col = c;

        const faces = ['top', 'bottom', 'left', 'right', 'front', 'back'];
        faces.forEach(face => {
          const faceDiv = document.createElement('div');
          faceDiv.className = `cube-face cube-face--${face}`;
          cube.appendChild(faceDiv);
        });

        scene.appendChild(cube);
      }
    }

    wrapper.appendChild(scene);
    this.container.appendChild(wrapper);
    this.sceneRef = scene;
  }

  tiltAt(rowCenter, colCenter) {
    if (!this.sceneRef) return;
    
    this.sceneRef.querySelectorAll('.cube').forEach(cube => {
      const r = +cube.dataset.row;
      const c = +cube.dataset.col;
      const dist = Math.hypot(r - rowCenter, c - colCenter);
      
      if (dist <= this.options.radius) {
        const pct = 1 - dist / this.options.radius;
        const angle = pct * this.options.maxAngle;
        
        gsap.to(cube, {
          duration: this.options.enterDuration,
          ease: this.options.easing,
          overwrite: true,
          rotateX: -angle,
          rotateY: angle
        });
      } else {
        gsap.to(cube, {
          duration: this.options.leaveDuration,
          ease: 'power3.out',
          overwrite: true,
          rotateX: 0,
          rotateY: 0
        });
      }
    });
  }

  onPointerMove = (e) => {
    this.userActive = true;
    if (this.idleTimer) clearTimeout(this.idleTimer);

    const rect = this.sceneRef.getBoundingClientRect();
    const cellW = rect.width / this.options.gridSize;
    const cellH = rect.height / this.options.gridSize;
    const colCenter = (e.clientX - rect.left) / cellW;
    const rowCenter = (e.clientY - rect.top) / cellH;

    if (this.rafRef) cancelAnimationFrame(this.rafRef);
    this.rafRef = requestAnimationFrame(() => this.tiltAt(rowCenter, colCenter));

    this.idleTimer = setTimeout(() => {
      this.userActive = false;
    }, 3000);
  }

  resetAll = () => {
    if (!this.sceneRef) return;
    this.sceneRef.querySelectorAll('.cube').forEach(cube =>
      gsap.to(cube, {
        duration: this.options.leaveDuration,
        rotateX: 0,
        rotateY: 0,
        ease: 'power3.out'
      })
    );
  }

  onClick = (e) => {
    if (!this.options.rippleOnClick || !this.sceneRef) return;
    
    const rect = this.sceneRef.getBoundingClientRect();
    const cellW = rect.width / this.options.gridSize;
    const cellH = rect.height / this.options.gridSize;

    const colHit = Math.floor((e.clientX - rect.left) / cellW);
    const rowHit = Math.floor((e.clientY - rect.top) / cellH);

    const baseRingDelay = 0.15;
    const baseAnimDur = 0.3;
    const baseHold = 0.6;

    const spreadDelay = baseRingDelay / this.options.rippleSpeed;
    const animDuration = baseAnimDur / this.options.rippleSpeed;
    const holdTime = baseHold / this.options.rippleSpeed;

    const rings = {};
    this.sceneRef.querySelectorAll('.cube').forEach(cube => {
      const r = +cube.dataset.row;
      const c = +cube.dataset.col;
      const dist = Math.hypot(r - rowHit, c - colHit);
      const ring = Math.round(dist);
      if (!rings[ring]) rings[ring] = [];
      rings[ring].push(cube);
    });

    Object.keys(rings)
      .map(Number)
      .sort((a, b) => a - b)
      .forEach(ring => {
        const delay = ring * spreadDelay;
        const faces = rings[ring].flatMap(cube => 
          Array.from(cube.querySelectorAll('.cube-face'))
        );

        gsap.to(faces, {
          backgroundColor: this.options.rippleColor,
          duration: animDuration,
          delay,
          ease: 'power3.out'
        });
        gsap.to(faces, {
          backgroundColor: this.options.faceColor,
          duration: animDuration,
          delay: delay + animDuration + holdTime,
          ease: 'power3.out'
        });
      });
  }

  startAutoAnimation() {
    this.simPos = {
      x: Math.random() * this.options.gridSize,
      y: Math.random() * this.options.gridSize
    };
    this.simTarget = {
      x: Math.random() * this.options.gridSize,
      y: Math.random() * this.options.gridSize
    };

    const speed = 0.02;
    const loop = () => {
      if (!this.userActive) {
        this.simPos.x += (this.simTarget.x - this.simPos.x) * speed;
        this.simPos.y += (this.simTarget.y - this.simPos.y) * speed;
        this.tiltAt(this.simPos.y, this.simPos.x);

        if (Math.hypot(this.simPos.x - this.simTarget.x, this.simPos.y - this.simTarget.y) < 0.1) {
          this.simTarget = {
            x: Math.random() * this.options.gridSize,
            y: Math.random() * this.options.gridSize
          };
        }
      }
      this.simRAF = requestAnimationFrame(loop);
    };
    this.simRAF = requestAnimationFrame(loop);
  }

  bindEvents() {
    this.sceneRef.addEventListener('pointermove', this.onPointerMove);
    this.sceneRef.addEventListener('pointerleave', this.resetAll);
    this.sceneRef.addEventListener('click', this.onClick);
  }

  destroy() {
    if (this.sceneRef) {
      this.sceneRef.removeEventListener('pointermove', this.onPointerMove);
      this.sceneRef.removeEventListener('pointerleave', this.resetAll);
      this.sceneRef.removeEventListener('click', this.onClick);
    }
    if (this.rafRef) cancelAnimationFrame(this.rafRef);
    if (this.simRAF) cancelAnimationFrame(this.simRAF);
    if (this.idleTimer) clearTimeout(this.idleTimer);
  }
}
