<template>
  <div class="interactive-progress" v-if="visible">
    <q-card flat bordered class="progress-card">
      <q-card-section>
        <div class="text-h6 q-mb-md text-center">
          <q-icon :name="currentStageIcon" size="32px" color="primary" class="pulse-animation" />
          <div class="q-mt-sm">{{ currentStageText }}</div>
        </div>

        <div class="stages-container">
          <div
            v-for="(stage, idx) in stages"
            :key="idx"
            class="stage-item"
            :class="{
              'stage-active': idx === currentStage,
              'stage-completed': idx < currentStage
            }"
          >
            <div class="stage-circle">
              <q-icon
                :name="idx < currentStage ? 'mdi-check' : stage.icon"
                size="24px"
                :color="idx <= currentStage ? 'white' : 'grey-5'"
              />
            </div>
            <div class="stage-label">{{ stage.label }}</div>
            <div class="stage-connector" v-if="idx < stages.length - 1"></div>
          </div>
        </div>

        <q-linear-progress
          :value="overallProgress"
          color="primary"
          size="12px"
          rounded
          class="q-mt-lg"
        />

        <div class="text-center text-caption text-grey-7 q-mt-sm">
          {{ Math.round(overallProgress * 100) }}% завершено
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'

export default defineComponent({
  name: 'InteractiveProgress',

  props: {
    visible: {
      type: Boolean,
      default: false
    },
    stage: {
      type: String,
      default: 'validation'
    }
  },

  setup(props) {
    const stages = [
      { key: 'validation', label: 'Валідація запиту', icon: 'mdi-shield-check' },
      { key: 'retrieval', label: 'Пошук релевантних джерел', icon: 'mdi-database-search' },
      { key: 'generation', label: 'Генерація відповіді', icon: 'mdi-creation' },
      { key: 'evaluation', label: 'Оцінка якості відповіді', icon: 'mdi-chart-line' }
    ]

    const currentStage = ref(0)

    const currentStageIcon = computed(() => {
      return stages[currentStage.value]?.icon || 'mdi-loading'
    })

    const currentStageText = computed(() => {
      return stages[currentStage.value]?.label || 'Обробка...'
    })

    const overallProgress = computed(() => {
      return (currentStage.value + 1) / stages.length
    })

    watch(() => props.stage, (newStage) => {
      const idx = stages.findIndex(s => s.key === newStage)
      if (idx !== -1) {
        currentStage.value = idx
      }
    })

    watch(() => props.visible, (newVal) => {
      if (!newVal) {
        currentStage.value = 0
      }
    })

    return {
      stages,
      currentStage,
      currentStageIcon,
      currentStageText,
      overallProgress
    }
  }
})
</script>

<style lang="scss" scoped>
.interactive-progress {
  margin: 20px 0;
}

.progress-card {
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.02) 0%, rgba(156, 39, 176, 0.02) 100%);
}

.stages-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  padding: 20px 0;
}

.stage-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
}

.stage-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #E0E0E0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.5s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stage-active .stage-circle {
  background: linear-gradient(135deg, #1976D2 0%, #2196F3 100%);
  transform: scale(1.15);
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.4);
  animation: pulse-ring 2s infinite;
}

.stage-completed .stage-circle {
  background: #4CAF50;
}

.stage-label {
  margin-top: 8px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  color: #666;
  transition: all 0.3s ease;
}

.stage-active .stage-label {
  color: #1976D2;
  font-weight: 700;
  transform: scale(1.05);
}

.stage-completed .stage-label {
  color: #4CAF50;
}

.stage-connector {
  position: absolute;
  top: 28px;
  left: 56px;
  right: -50%;
  height: 3px;
  background: #E0E0E0;
  z-index: -1;
}

.stage-completed .stage-connector {
  background: linear-gradient(90deg, #4CAF50 0%, #E0E0E0 100%);
}

.pulse-animation {
  animation: pulse-icon 1.5s infinite;
}

@keyframes pulse-icon {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes pulse-ring {
  0% {
    box-shadow: 0 4px 16px rgba(25, 118, 210, 0.4),
                0 0 0 0 rgba(25, 118, 210, 0.7);
  }
  50% {
    box-shadow: 0 4px 16px rgba(25, 118, 210, 0.4),
                0 0 0 10px rgba(25, 118, 210, 0);
  }
  100% {
    box-shadow: 0 4px 16px rgba(25, 118, 210, 0.4),
                0 0 0 0 rgba(25, 118, 210, 0);
  }
}

@media (max-width: 600px) {
  .stages-container {
    flex-direction: column;
    gap: 20px;
  }

  .stage-connector {
    display: none;
  }
}
</style>
