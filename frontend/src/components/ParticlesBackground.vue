<template>
  <div class="particles-background">
    <div
      v-for="particle in particles"
      :key="particle.id"
      class="particle"
      :style="{
        left: particle.x + '%',
        top: particle.y + '%',
        width: particle.size + 'px',
        height: particle.size + 'px',
        animationDuration: particle.duration + 's',
        animationDelay: particle.delay + 's',
        opacity: particle.opacity
      }"
    ></div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue'

export default defineComponent({
  name: 'ParticlesBackground',

  setup() {
    const particles = ref([])

    const generateParticles = () => {
      const particleArray = []
      for (let i = 0; i < 50; i++) {
        particleArray.push({
          id: i,
          x: Math.random() * 100,
          y: Math.random() * 100,
          size: 2 + Math.random() * 4,
          duration: 10 + Math.random() * 20,
          delay: Math.random() * 5,
          opacity: 0.1 + Math.random() * 0.3
        })
      }
      particles.value = particleArray
    }

    onMounted(() => {
      generateParticles()
    })

    return {
      particles
    }
  }
})
</script>

<style lang="scss" scoped>
.particles-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: radial-gradient(circle, #1976D2 0%, transparent 70%);
  border-radius: 50%;
  animation: float infinite ease-in-out;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) translateX(0);
  }
  25% {
    transform: translateY(-20px) translateX(10px);
  }
  50% {
    transform: translateY(-40px) translateX(-10px);
  }
  75% {
    transform: translateY(-20px) translateX(10px);
  }
}
</style>
