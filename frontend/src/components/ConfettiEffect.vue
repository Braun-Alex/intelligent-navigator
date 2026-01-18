<template>
  <div class="confetti-container" v-if="active">
    <div
      v-for="confetti in confettiPieces"
      :key="confetti.id"
      class="confetti"
      :style="{
        left: confetti.x + '%',
        backgroundColor: confetti.color,
        animationDuration: confetti.duration + 's',
        animationDelay: confetti.delay + 's'
      }"
    ></div>
  </div>
</template>

<script>
import { defineComponent, ref, watch } from 'vue'

export default defineComponent({
  name: 'ConfettiEffect',

  props: {
    active: {
      type: Boolean,
      default: false
    },
    duration: {
      type: Number,
      default: 3000
    }
  },

  setup(props) {
    const confettiPieces = ref([])

    const colors = [
      '#1976D2', '#2196F3', '#64B5F6',
      '#4CAF50', '#8BC34A', '#CDDC39',
      '#FF9800', '#FF5722', '#F44336',
      '#9C27B0', '#E91E63', '#FF4081'
    ]

    const generateConfetti = () => {
      const pieces = []
      for (let i = 0; i < 100; i++) {
        pieces.push({
          id: i,
          x: Math.random() * 100,
          color: colors[Math.floor(Math.random() * colors.length)],
          duration: 2 + Math.random() * 2,
          delay: Math.random() * 0.5
        })
      }
      confettiPieces.value = pieces
    }

    watch(() => props.active, (newVal) => {
      if (newVal) {
        generateConfetti()
        setTimeout(() => {
          confettiPieces.value = []
        }, props.duration)
      }
    })

    return {
      confettiPieces
    }
  }
})
</script>

<style lang="scss" scoped>
.confetti-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10000;
  overflow: hidden;
}

.confetti {
  position: absolute;
  width: 10px;
  height: 10px;
  top: -10px;
  opacity: 0;
  animation: confetti-fall linear forwards;
}

@keyframes confetti-fall {
  0% {
    opacity: 1;
    top: -10px;
    transform: rotate(0deg);
  }
  100% {
    opacity: 0;
    top: 100vh;
    transform: rotate(720deg);
  }
}
</style>
