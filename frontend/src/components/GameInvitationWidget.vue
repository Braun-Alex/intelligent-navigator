<template>
  <transition name="slide-down">
    <div v-if="visible" class="game-invitation-widget" @click="openGame">
      <q-card flat bordered class="invitation-card">
        <q-card-section class="invitation-content">
          <div class="mini-dino-animation">
            <div class="mini-dino">
              <div class="dino-body"></div>
              <div class="dino-head"></div>
              <div class="dino-eye"></div>
              <div class="dino-leg leg-1"></div>
              <div class="dino-leg leg-2"></div>
            </div>
            <div class="mini-cactus"></div>
          </div>
          
          <div class="invitation-text">
            <div class="text-subtitle2 text-weight-bold">🎮 Чекаєте відповідь?</div>
            <div class="text-caption">Пограйте в Dino Runner!</div>
          </div>
          
          <q-icon name="mdi-chevron-right" size="24px" color="primary" class="pulse-icon" />
        </q-card-section>
      </q-card>
    </div>
  </transition>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'GameInvitationWidget',

  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },

  emits: ['open-game'],

  setup(_, { emit }) {
    const openGame = () => {
      emit('open-game')
    }

    return {
      openGame
    }
  }
})
</script>

<style lang="scss" scoped>
.game-invitation-widget {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9000;
  cursor: pointer;
  animation: float 3s ease-in-out infinite;
}

.invitation-card {
  border-radius: 16px;
  background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
  box-shadow: 0 8px 24px rgba(76, 175, 80, 0.4);
  border: 2px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 12px 32px rgba(76, 175, 80, 0.6);
  }
}

.invitation-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: white;
}

.invitation-text {
  flex: 1;
}

.pulse-icon {
  animation: pulse-scale 1.5s infinite;
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

// Міні-анімація динозавра
.mini-dino-animation {
  position: relative;
  width: 60px;
  height: 40px;
}

.mini-dino {
  position: absolute;
  left: 5px;
  bottom: 5px;
  animation: mini-run 1.5s infinite;
}

.dino-body {
  width: 16px;
  height: 16px;
  background: #FFFFFF;
  border-radius: 2px;
  position: relative;
}

.dino-head {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 8px;
  height: 8px;
  background: #FFFFFF;
  border-radius: 1px;
}

.dino-eye {
  position: absolute;
  top: -5px;
  right: -3px;
  width: 2px;
  height: 2px;
  background: #000;
  border-radius: 50%;
}

.dino-leg {
  position: absolute;
  width: 3px;
  height: 6px;
  background: #FFFFFF;
  bottom: -6px;
}

.leg-1 {
  left: 2px;
  animation: leg-move 0.4s infinite;
}

.leg-2 {
  right: 2px;
  animation: leg-move 0.4s infinite 0.2s;
}

@keyframes leg-move {
  0%, 100% { height: 6px; }
  50% { height: 4px; }
}

.mini-cactus {
  position: absolute;
  right: 5px;
  bottom: 5px;
  width: 8px;
  height: 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 1px;
  animation: cactus-move 2s linear infinite;
}

@keyframes cactus-move {
  0% { transform: translateX(0); opacity: 1; }
  100% { transform: translateX(-60px); opacity: 0; }
}

@keyframes mini-run {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

// Анімації появи і зникнення
.slide-down-enter-active {
  animation: slideDown 0.5s ease;
}

.slide-down-leave-active {
  animation: slideUp 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-100%);
  }
}
</style>
