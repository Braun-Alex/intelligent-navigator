<template>
  <div>
    <!-- Конфетті -->
    <ConfettiEffect :active="showConfetti" :duration="duration" />
    
    <!-- Випадкове повідомлення -->
    <transition name="fade">
      <div v-if="showMessage" class="easter-egg-message" :class="messageType">
        <q-card flat bordered class="message-card">
          <q-card-section class="row items-center">
            <q-icon :name="messageIcon" size="48px" :color="messageColor" class="q-mr-md" />
            <div class="col">
              <div class="text-h6 text-weight-bold">{{ messageTitle }}</div>
              <div class="text-body2 q-mt-xs">{{ messageText }}</div>
            </div>
            <q-btn
              flat
              round
              dense
              icon="mdi-close"
              @click="hideMessage"
              class="q-ml-md"
            />
          </q-card-section>
        </q-card>
      </div>
    </transition>

    <!-- Анімовані емодзі -->
    <transition name="fade">
      <div v-if="showEmoji" class="floating-emoji">
        {{ currentEmoji }}
      </div>
    </transition>
  </div>
</template>

<script>
import { defineComponent, ref } from 'vue'
import ConfettiEffect from './ConfettiEffect.vue'

export default defineComponent({
  name: 'RandomEasterEggs',

  components: {
    ConfettiEffect
  },

  setup() {
    const showConfetti = ref(false)
    const duration = ref(3000)
    const showMessage = ref(false)
    const showEmoji = ref(false)
    const currentEmoji = ref('🎉')
    const messageType = ref('success')
    const messageIcon = ref('mdi-party-popper')
    const messageColor = ref('positive')
    const messageTitle = ref('')
    const messageText = ref('')

    // Статистика для відстеження
    let totalQueries = 0
    let totalSuccessfulResponses = 0
    let consecutiveQueries = 0
    let lastQueryTime = 0

    // База даних Easter Eggs
    const easterEggs = {
      // Після успішної відповіді
      onSuccessfulResponse: [
        {
          probability: 1, // Завжди з'являється після надання відповіді на запит
          type: 'confetti',
          message: {
            title: '🎊 Відповідь згенеровано!',
            text: 'Сподіваймося, ця інформація Вам допоможе!',
            icon: 'mdi-check-decagram',
            color: 'positive'
          }
        },
        {
          probability: 0.09,
          type: 'emoji',
          emoji: '🦖',
          message: {
            title: '🦖 Dino Runner вітає!',
            text: 'Очікуєте відповідь на запит? Пограйте в Dino Runner!',
            icon: 'mdi-google-controller',
            color: 'info'
          }
        },
        {
          probability: 0.15,
          type: 'message',
          message: {
            title: '💡 Корисна інформація!',
            text: 'Ви завжди можете оцінити якість відповіді!',
            icon: 'mdi-lightbulb-on',
            color: 'warning'
          }
        }
      ],

      // Після певної кількості запитів
      onMilestone: [
        {
          milestone: 5,
          type: 'confetti',
          message: {
            title: '🌟 5 запитів!',
            text: 'Ви активно використовуєте систему!',
            icon: 'mdi-star-circle',
            color: 'primary'
          }
        },
        {
          milestone: 10,
          type: 'confetti',
          message: {
            title: '🏆 10 запитів!',
            text: 'Справжній дослідник документів!',
            icon: 'mdi-trophy',
            color: 'accent'
          }
        },
        {
          milestone: 30,
          type: 'confetti',
          message: {
            title: '🎯 30 запитів!',
            text: 'Яке завзяття! Дякуємо за активність!',
            icon: 'mdi-emoticon-excited',
            color: 'positive'
          }
        }
      ],

      // При високій якості відповіді (більше 0.9)
      onHighQuality: [
        {
          probability: 0.15,
          type: 'confetti',
          message: {
            title: '⭐ Відмінна якість!',
            text: 'Відповідь отримала високу оцінку!',
            icon: 'mdi-star-face',
            color: 'positive'
          }
        }
      ],

      // При швидкій відповіді (менше 9 секунд)
      onFastResponse: [
        {
          probability: 0.3,
          type: 'emoji',
          emoji: '⚡',
          message: {
            title: '⚡ Відповідь отримано швидко!',
            text: 'Відповідь отримано менше, ніж за 9 секунд!',
            icon: 'mdi-flash',
            color: 'warning'
          }
        }
      ],

      // Випадковий Easter Egg
      random: [
        {
          probability: 0.03,
          type: 'confetti',
          message: {
            title: '🎲 Дякуємо!',
            text: 'Дякуємо за користування системою!',
            icon: 'mdi-dice-multiple',
            color: 'secondary'
          }
        },
        {
          probability: 0.01,
          type: 'emoji',
          emoji: '🎪',
          message: {
            title: '🎪 Наша вдячність!',
            text: 'Завжди раді прийти на допомогу з пошуком інформації!',
            icon: 'mdi-auto-fix',
            color: 'accent'
          }
        }
      ],

      // При багатьох послідовних запитах
      onConsecutiveQueries: [
        {
          threshold: 3, // 3 запити підряд менше, ніж за 15 хвилин
          probability: 0.9,
          type: 'message',
          message: {
            title: '🔥 Активний дослідник!',
            text: 'Схоже, ви шукаєте багато інформації!',
            icon: 'mdi-fire',
            color: 'negative'
          }
        }
      ]
    }

    // Перевірка та запуск Easter Egg
    const checkAndTrigger = (eggs, condition = true) => {
      if (!condition) return false

      for (const egg of eggs) {
        const chance = Math.random()
        if (chance < egg.probability) {
          triggerEasterEgg(egg)
          return true
        }
      }
      return false
    }

    // Запуск Easter Egg
    const triggerEasterEgg = (egg) => {
      if (egg.type === 'confetti') {
        showConfetti.value = true
        setTimeout(() => {
          showConfetti.value = false
        }, duration.value)
      }

      if (egg.type === 'emoji') {
        currentEmoji.value = egg.emoji || '🎉'
        showEmoji.value = true
        setTimeout(() => {
          showEmoji.value = false
        }, 3000)
      }

      if (egg.message) {
        messageTitle.value = egg.message.title
        messageText.value = egg.message.text
        messageIcon.value = egg.message.icon
        messageColor.value = egg.message.color
        showMessage.value = true
        
        setTimeout(() => {
          showMessage.value = false
        }, 5000)
      }
    }

    // API-методи
    const onSuccessfulResponse = (responseData = {}) => {
      totalSuccessfulResponses++
      
      // Перевірка випадкового Easter Egg
      checkAndTrigger(easterEggs.random)
      
      // Перевірка основного Easter Egg після успішної відповіді
      if (!checkAndTrigger(easterEggs.onSuccessfulResponse)) {
        // Якщо не спрацював основний, перевіряємо інші умови
        
        // Швидка відповідь
        if (responseData.responseTime && responseData.responseTime < 9) {
          checkAndTrigger(easterEggs.onFastResponse)
        }
        
        // Висока якість
        if (responseData.quality && responseData.quality > 0.9) {
          checkAndTrigger(easterEggs.onHighQuality)
        }
      }
    }

    const onQuerySubmitted = () => {
      totalQueries++
      
      // Перевірка Milestone
      const milestone = easterEggs.onMilestone.find(m => m.milestone === totalQueries)
      if (milestone) {
        triggerEasterEgg(milestone)
        return
      }
      
      // Перевірка послідовних запитів
      const now = Date.now()
      if (now - lastQueryTime < 900000) { // 15 хвилин
        consecutiveQueries++
        
        const consecutiveEgg = easterEggs.onConsecutiveQueries.find(
          e => consecutiveQueries >= e.threshold
        )
        if (consecutiveEgg) {
          checkAndTrigger([consecutiveEgg])
        }
      } else {
        consecutiveQueries = 1
      }
      lastQueryTime = now
      
      // Випадковий Easter Egg
      checkAndTrigger(easterEggs.random)
    }

    const hideMessage = () => {
      showMessage.value = false
    }

    const getStats = () => {
      return {
        totalQueries,
        totalSuccessfulResponses,
        consecutiveQueries
      }
    }

    const reset = () => {
      totalQueries = 0
      totalSuccessfulResponses = 0
      consecutiveQueries = 0
      lastQueryTime = 0
    }

    return {
      showConfetti,
      duration,
      showMessage,
      showEmoji,
      currentEmoji,
      messageType,
      messageIcon,
      messageColor,
      messageTitle,
      messageText,
      onSuccessfulResponse,
      onQuerySubmitted,
      hideMessage,
      getStats,
      reset
    }
  }
})
</script>

<style lang="scss" scoped>
.easter-egg-message {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 10000;
  max-width: 400px;
  animation: slideInRight 0.5s ease;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.message-card {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border-left: 4px solid;
  
  &.success {
    border-left-color: #4CAF50;
  }
  
  &.info {
    border-left-color: #2196F3;
  }
  
  &.warning {
    border-left-color: #FF9800;
  }
}

.floating-emoji {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 120px;
  z-index: 9998;
  animation: emojiFloat 3s ease-out forwards;
  pointer-events: none;
}

@keyframes emojiFloat {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5) rotate(0deg);
  }
  50% {
    opacity: 1;
    transform: translate(-50%, -60%) scale(1.2) rotate(180deg);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -70%) scale(1.5) rotate(360deg);
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
