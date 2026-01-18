<template>
  <q-page class="flex flex-center bg-pattern">
    <!-- Частинки на фоні -->
    <ParticlesBackground />

    <!-- Система випадкових Easter Eggs -->
    <RandomEasterEggs ref="easterEggsRef" />

    <!-- Запрошення до гри (маленьке вікно) -->
    <GameInvitationWidget 
      :visible="showGameInvitation" 
      @open-game="openDinoGame"
    />

    <!-- Графічна міні-гра Dino Runner -->
    <DinoRunnerGame 
      :visible="showDinoGame" 
      @close="closeDinoGame"
    />

    <div class="container q-pa-md">
      <div class="text-center q-mb-xl animated-header" v-if="!hasSearched">
        <div class="icon-wrapper">
          <q-icon
            name="mdi-book-search"
            size="80px"
            color="primary"
            class="animated-icon"
          />
        </div>
        <h1 class="text-h3 text-weight-bold q-mt-md q-mb-sm gradient-text">
          Інтелектуальний навігатор
        </h1>
        <p class="text-h6 text-grey-7 typing-animation">
          Я тут, щоб Вам допомогти. Ставте запитання
        </p>
      </div>

      <!-- Секція пошуку -->
      <div class="search-container q-mb-lg">
        <q-card flat bordered class="search-card" :class="{ 'elevated-card': isFocused }">
          <q-card-section>
            <div class="row q-col-gutter-md">
              <div class="col-12">
                <q-input
                  v-model="question"
                  type="textarea"
                  outlined
                  autofocus
                  autogrow
                  :placeholder="placeholderText"
                  @focus="isFocused = true"
                  @blur="isFocused = false"
                  class="search-input"
                  :input-style="{ minHeight: '56px' }"
                  :disable="loading"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" size="28px" color="primary" class="search-icon-pulse" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      round
                      dense
                      flat
                      icon="close"
                      v-if="question && !loading"
                      @click="question = ''"
                      class="hover-rotate"
                    />
                  </template>
                  <template v-slot:hint>
                    Ctrl+Enter для пошуку
                  </template>
                </q-input>
              </div>

              <div class="col-12">
                <div class="row items-center justify-between">
                  <div class="col-auto">
                    <q-toggle
                      v-model="showContexts"
                      label="Показати джерела"
                      color="primary"
                      left-label
                      :disable="loading"
                      class="animated-toggle"
                    />
                    <q-toggle
                      v-model="showEvaluation"
                      label="Оцінити якість"
                      color="secondary"
                      left-label
                      class="q-ml-md animated-toggle"
                      :disable="loading"
                    />
                  </div>

                  <div class="col-auto">
                    <q-btn
                      unelevated
                      rounded
                      color="primary"
                      :label="loading ? streamingStatus : 'Знайти відповідь'"
                      icon="mdi-magnify"
                      size="lg"
                      @click="handleSearch"
                      :loading="loading"
                      :disable="!question.trim() || loading"
                      class="search-button glowing-button"
                    >
                      <template v-slot:loading>
                        <div class="row items-center">
                          <q-spinner-dots color="white" size="20px" class="q-mr-sm" />
                          <span>{{ streamingStatus }}</span>
                        </div>
                      </template>
                    </q-btn>
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>

          <q-linear-progress
            v-if="loading"
            indeterminate
            color="primary"
            size="4px"
          />
        </q-card>

        <!-- Інтерактивний прогрес -->
        <InteractiveProgress
          :visible="loading"
          :stage="currentProcessStage"
        />

        <!-- Інформація про швидкість -->
        <transition name="fade">
          <div class="q-mt-md" v-if="responseTime && !loading">
            <q-chip
              outline
              color="positive"
              text-color="positive"
              icon="mdi-speedometer"
              size="sm"
              class="bounce-in"
            >
              Час відповіді: {{ responseTime }} с
            </q-chip>
            <q-chip
              outline
              color="info"
              text-color="info"
              icon="mdi-file-multiple"
              size="sm"
              class="q-ml-sm bounce-in"
              v-if="contexts.length > 0"
            >
              {{ contexts.length }} джерел
            </q-chip>
          </div>
        </transition>
      </div>

      <!-- Секція відповіді -->
      <transition
        appear
        enter-active-class="animated fadeIn"
        leave-active-class="animated fadeOut"
      >
        <div v-if="hasSearched" class="results-container">
          <!-- Повідомлення про валідацію -->
          <transition name="shake">
            <q-banner
              v-if="validationFailed"
              class="bg-negative text-white q-mb-md validation-banner"
              rounded
            >
              <template v-slot:avatar>
                <q-icon name="mdi-shield-alert" size="48px" class="shake-animation" />
              </template>
              <div class="text-h6 text-weight-bold">Запит відхилено</div>
              <div class="text-body1 q-mt-sm">{{ validationReason }}</div>
            </q-banner>
          </transition>

          <!-- Відповідь -->
          <q-card flat bordered class="answer-card q-mb-md card-hover" v-if="!validationFailed">
            <q-card-section>
              <div class="row items-center q-mb-md">
                <q-icon name="mdi-comment-quote" size="32px" color="primary" class="q-mr-sm icon-bounce" />
                <span class="text-h5 text-weight-bold">Відповідь</span>
                <q-space />
                <q-chip
                  v-if="isStreaming"
                  color="primary"
                  text-color="white"
                  size="sm"
                  icon="mdi-wifi"
                  class="streaming-chip"
                >
                  <q-spinner-dots color="white" size="16px" class="q-mr-xs" />
                  Генерується...
                </q-chip>
              </div>
              
              <div class="answer-content streaming-text" v-html="formattedAnswer"></div>
              <span v-if="isStreaming" class="streaming-cursor">|</span>
            </q-card-section>

            <!-- Оцінка якості -->
            <q-card-section v-if="showEvaluation && (evaluation || evaluationPending)" class="bg-blue-grey-1">
              <div class="text-subtitle1 text-weight-bold q-mb-sm">
                <q-icon name="mdi-chart-bar" class="q-mr-sm" />
                Оцінка якості відповіді
              </div>

              <div v-if="evaluationPending && !evaluation" class="text-center q-pa-md">
                <q-spinner-dots color="primary" size="40px" />
                <div class="text-body2 text-grey-7 q-mt-sm">
                  Проводиться оцінка якості відповіді...
                </div>
              </div>

              <transition name="fade">
                <div v-if="evaluation">
                  <q-banner
                    :class="`q-mb-md quality-banner quality-${overallQuality.level}`"
                    rounded
                  >
                    <template v-slot:avatar>
                      <q-icon
                        :name="overallQuality.icon"
                        :color="overallQuality.color"
                        size="48px"
                        class="pulse-animation"
                      />
                    </template>
                    <div class="text-h6 text-weight-bold">{{ overallQuality.title }}</div>
                    <div class="text-body2 q-mt-xs">{{ overallQuality.description }}</div>
                  </q-banner>

                  <div class="row q-col-gutter-md">
                    <div class="col-6 col-md-4 col-lg-2" v-for="(metric, key) in metricsDisplay" :key="key">
                      <q-card flat class="metric-card card-hover">
                        <q-card-section class="text-center">
                          <div class="text-h4 text-weight-bold counter-animation" :class="getMetricColor(metric.value)">
                            {{ (metric.value * 100).toFixed(0) }}%
                          </div>
                          <div class="text-caption text-weight-bold text-grey-8">{{ metric.label }}</div>
                          <q-linear-progress
                            :value="metric.value"
                            :color="getMetricColorName(metric.value)"
                            size="8px"
                            rounded
                            class="q-mt-sm"
                          />
                        </q-card-section>
                      </q-card>
                    </div>
                  </div>
                </div>
              </transition>
            </q-card-section>
          </q-card>

          <!-- Контексти -->
          <q-card flat bordered class="contexts-card card-hover" v-if="showContexts && contexts.length > 0">
            <q-card-section>
              <div class="row items-center q-mb-lg">
                <q-icon name="mdi-file-document-multiple" size="32px" color="secondary" class="q-mr-sm icon-bounce" />
                <span class="text-h5 text-weight-bold">Знайдені джерела ({{ contexts.length }})</span>
              </div>

              <div class="q-gutter-md">
                <transition-group name="stagger-fade">
                  <q-card
                    v-for="(context, idx) in contexts"
                    :key="idx"
                    flat
                    bordered
                    class="source-card card-hover"
                  >
                    <q-card-section class="source-header bg-grey-2">
                      <div class="row items-center justify-between">
                        <div class="col">
                          <div class="row items-center q-gutter-sm">
                            <q-icon
                              :name="getSourceIcon(context.source)"
                              size="24px"
                              :color="getSourceColor(idx)"
                              class="icon-pulse"
                            />
                            <div>
                              <div class="text-subtitle1 text-weight-bold">
                                {{ formatSourceName(context.source) }}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div class="col-auto">
                          <q-badge
                            :color="getSourceColor(idx)"
                            text-color="white"
                            :label="`${idx + 1}`"
                            class="badge-pulse"
                          />
                        </div>
                      </div>
                    </q-card-section>

                    <q-card-section>
                      <div
                        class="text-body2 text-grey-8 context-preview"
                        v-html="highlightKeyTerms(context.preview, context.key_terms || [])"
                      >
                      </div>
                    </q-card-section>

                    <q-expansion-item
                      v-if="context.content && context.content.length > 300"
                      icon="mdi-eye"
                      label="Переглянути повний текст"
                      header-class="text-primary"
                    >
                      <q-card-section class="bg-grey-1">
                        <div
                          class="text-body2"
                          style="white-space: pre-wrap; line-height: 1.6;"
                          v-html="highlightKeyTerms(context.content, context.key_terms || [])"
                        >
                        </div>
                      </q-card-section>
                    </q-expansion-item>

                    <q-card-section class="q-pt-none">
                      <q-separator class="q-mb-sm" />
                      <div class="row q-gutter-sm text-caption text-grey-7">
                        <q-chip dense square icon="mdi-text-box" size="sm">
                          {{ context.length || 0 }} символів
                        </q-chip>
                        <q-chip
                          dense
                          square
                          icon="mdi-file-document"
                          size="sm"
                          v-if="context.chunk_index !== undefined"
                        >
                          Фрагмент {{ context.chunk_index + 1 }}
                        </q-chip>
                      </div>
                    </q-card-section>
                  </q-card>
                </transition-group>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </transition>
    </div>
  </q-page>
</template>

<script>
import { defineComponent, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useQuasar } from 'quasar'
import { marked } from 'marked'
import ParticlesBackground from '@/components/ParticlesBackground.vue'
import RandomEasterEggs from '@/components/RandomEasterEggs.vue'
import GameInvitationWidget from '@/components/GameInvitationWidget.vue'
import DinoRunnerGame from '@/components/DinoRunnerGame.vue'
import InteractiveProgress from '@/components/InteractiveProgress.vue'

export default defineComponent({
  name: 'IndexPage',

  components: {
    ParticlesBackground,
    RandomEasterEggs,
    GameInvitationWidget,
    DinoRunnerGame,
    InteractiveProgress
  },

  setup() {
    const $q = useQuasar()
    const question = ref('')
    const answer = ref('')
    const contexts = ref([])
    const evaluation = ref(null)
    const evaluationPending = ref(false)
    const loading = ref(false)
    const isStreaming = ref(false)
    const hasSearched = ref(false)
    const isFocused = ref(false)
    const showContexts = ref(true)
    const showEvaluation = ref(true)
    const validationFailed = ref(false)
    const validationReason = ref('')
    const streamingStatus = ref('Перевірка...')
    const responseTime = ref(null)
    const startTime = ref(null)
    const showGameInvitation = ref(false)
    const showDinoGame = ref(false)
    const currentProcessStage = ref('validation')
    const easterEggsRef = ref(null)

    const placeholderText = computed(() => {
      const placeholders = [
        'Сформулюйте своє запитання...',
        'Запитайте про освітній процес...',
        'Поставте своє запитання...'
      ]
      return placeholders[Math.floor(Math.random() * placeholders.length)]
    })

    const formattedAnswer = computed(() => {
      if (!answer.value) return ''
      return marked(answer.value)
    })

    const metricsDisplay = computed(() => {
      if (!evaluation.value) return []
      return {
        faithfulness: {
          label: 'Достовірність',
          value: evaluation.value.faithfulness
        },
        answer_relevancy: {
          label: 'Релевантність відповіді',
          value: evaluation.value.answer_relevancy
        },
        context_relevancy: {
          label: 'Релевантність контексту',
          value: evaluation.value.context_relevancy
        },
        mrr: {
          label: 'MRR',
          value: evaluation.value.mrr
        },
        map: {
          label: 'MAP',
          value: evaluation.value.map
        },
        overall_score: {
          label: 'Загальна оцінка',
          value: evaluation.value.overall_score
        }
      }
    })

    const overallQuality = computed(() => {
      if (!evaluation.value) return { level: 'unknown', title: '', description: '', icon: '', color: '' }

      const score = evaluation.value.overall_score

      if (score >= 0.85) {
        return {
          level: 'excellent',
          title: 'Відмінна якість відповіді',
          description: 'Відповідь повністю обґрунтована документами, точно відповідає на ваше питання і базується на релевантних джерелах. Можете довіряти цій інформації.',
          icon: 'mdi-check-decagram',
          color: 'positive'
        }
      } else if (score >= 0.70) {
        return {
          level: 'good',
          title: 'Гарна якість відповіді',
          description: 'Відповідь, загалом, є надійною і підтверджується документами. Можливі незначні неточності або неповнота інформації.',
          icon: 'mdi-check-circle',
          color: 'positive'
        }
      } else if (score >= 0.50) {
        return {
          level: 'fair',
          title: 'Прийнятна якість відповіді',
          description: 'Відповідь може містити корисну інформацію, але краще перевірити деталі в оригінальних документах. Деякі аспекти можуть бути неповними.',
          icon: 'mdi-alert-circle',
          color: 'warning'
        }
      } else {
        return {
          level: 'low',
          title: 'Низька якість відповіді',
          description: 'Відповідь може бути неповною або неточною. Рекомендація: переформулювати питання або звернутися до оригінальних документів.',
          icon: 'mdi-alert',
          color: 'negative'
        }
      }
    })

    const getMetricColor = (value) => {
      if (value >= 0.8) return 'text-positive'
      if (value >= 0.6) return 'text-warning'
      return 'text-negative'
    }

    const getMetricColorName = (value) => {
      if (value >= 0.8) return 'positive'
      if (value >= 0.6) return 'warning'
      return 'negative'
    }

    // Відкриття гри із запрошення
    const openDinoGame = () => {
      showDinoGame.value = true
      showGameInvitation.value = false
    }

    // Закриття гри
    const closeDinoGame = () => {
      showDinoGame.value = false
      // Якщо все ще йде обробка - показуємо запрошення знову
      if (loading.value) {
        showGameInvitation.value = true
      }
    }

    // Обробка комбінації клавіш Ctrl + Enter для пошуку
    const handleCtrlEnter = (event) => {
      if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault()
        handleSearch()
      }
    }

    const handleSearch = async () => {
      if (!question.value.trim()) {
        $q.notify({
          type: 'warning',
          message: 'Будь ласка, введіть запитання',
          position: 'top'
        })
        return
      }

      // Повідомляємо Easter Eggs про новий запит
      if (easterEggsRef.value) {
        easterEggsRef.value.onQuerySubmitted()
      }

      loading.value = true
      isStreaming.value = false
      hasSearched.value = true
      answer.value = ''
      contexts.value = []
      evaluation.value = null
      evaluationPending.value = false
      validationFailed.value = false
      validationReason.value = ''
      responseTime.value = null
      streamingStatus.value = 'Перевірка запиту...'
      startTime.value = Date.now()
      currentProcessStage.value = 'validation'

      // Показуємо запрошення до гри через дві секунди
      const gameInvitationTimer = setTimeout(() => {
        if (loading.value) {
          showGameInvitation.value = true
        }
      }, 2000)

      try {
        const apiUrl = import.meta.env.DEV ? '/api' : 'http://localhost:8000'
        const eventSource = new EventSource(
          `${apiUrl}/query/stream?` + new URLSearchParams({
            question: question.value,
            return_contexts: showContexts.value,
            return_evaluation: showEvaluation.value
          })
        )

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            switch (data.type) {
              case 'validation':
                streamingStatus.value = 'Валідація пройдена'
                currentProcessStage.value = 'retrieval'
                if (!data.data.is_valid) {
                  validationFailed.value = true
                  validationReason.value = data.data.reason
                  loading.value = false
                  isStreaming.value = false
                  showGameInvitation.value = false
                  showDinoGame.value = false
                  clearTimeout(gameInvitationTimer)
                  eventSource.close()
                  
                  $q.notify({
                    type: 'warning',
                    message: 'Запит відхилено',
                    position: 'top'
                  })
                }
                break

              case 'contexts':
                streamingStatus.value = 'Знайдено джерела'
                currentProcessStage.value = 'generation'
                contexts.value = data.data.contexts
                break

              case 'token':
                if (!isStreaming.value) {
                  isStreaming.value = true
                  streamingStatus.value = 'Генерація відповіді'
                }
                answer.value += data.data.token
                break

              case 'evaluation_pending':
                evaluationPending.value = true
                currentProcessStage.value = 'evaluation'
                streamingStatus.value = 'Оцінка якості...'
                break

              case 'evaluation':
                evaluation.value = data.data
                evaluationPending.value = false
                break

              case 'evaluation_error':
                evaluationPending.value = false
                console.error('Evaluation error:', data.data.error)
                break

              case 'done':
                isStreaming.value = false
                loading.value = false
                showGameInvitation.value = false
                clearTimeout(gameInvitationTimer)
                eventSource.close()
                
                const elapsed = ((Date.now() - startTime.value) / 1000).toFixed(1)
                responseTime.value = elapsed
                
                // Повідомляємо Easter Eggs про успішну відповідь
                if (easterEggsRef.value) {
                  easterEggsRef.value.onSuccessfulResponse({
                    responseTime: parseFloat(elapsed),
                    quality: evaluation.value?.overall_score || 0
                  })
                }
                
                $q.notify({
                  type: 'positive',
                  message: `Відповідь отримано за ${elapsed} с!`,
                  position: 'top',
                  icon: 'mdi-check-circle'
                })
                break

              case 'error':
                loading.value = false
                isStreaming.value = false
                showGameInvitation.value = false
                showDinoGame.value = false
                clearTimeout(gameInvitationTimer)
                eventSource.close()
                
                $q.notify({
                  type: 'negative',
                  message: data.data.message || 'Помилка при обробці запиту',
                  position: 'top'
                })
                break
            }
          } catch (error) {
            console.error('Помилка при обробці SSE-даних:', error)
          }
        }

        eventSource.onerror = (error) => {
          console.error('SSE-помилка:', error)
          loading.value = false
          isStreaming.value = false
          showGameInvitation.value = false
          showDinoGame.value = false
          clearTimeout(gameInvitationTimer)
          eventSource.close()
          
          $q.notify({
            type: 'negative',
            message: 'Помилка з\'єднання із сервером',
            position: 'top'
          })
        }

      } catch (error) {
        console.error('Помилка пошуку:', error)
        loading.value = false
        isStreaming.value = false
        showGameInvitation.value = false
        showDinoGame.value = false
        clearTimeout(gameInvitationTimer)
        
        $q.notify({
          type: 'negative',
          message: 'Помилка при отриманні відповіді',
          position: 'top'
        })
      }
    }

    const formatSourceName = (source) => {
      if (!source) return 'Невідоме джерело'
      let name = source.replace('.pdf', '').replace(/-/g, ' ').replace(/_/g, ' ')
      if (name.length > 60) name = name.substring(0, 57) + '...'
      return name
    }

    const getSourceIcon = (source) => {
      if (!source) return 'mdi-file-document'
      const sourceLower = source.toLowerCase()
      if (sourceLower.includes('polozhennia') || sourceLower.includes('положення')) {
        return 'mdi-book-open-variant'
      }
      if (sourceLower.includes('integrity') || sourceLower.includes('доброчесн')) {
        return 'mdi-shield-check'
      }
      return 'mdi-file-document-outline'
    }

    const getSourceColor = (idx) => {
      const colors = ['primary', 'secondary', 'accent', 'positive', 'info']
      return colors[idx % colors.length]
    }

    const highlightKeyTerms = (text, keyTerms) => {
      if (!text || !keyTerms || keyTerms.length === 0) return text
      
      let highlightedText = text
      const sortedTerms = [...keyTerms].sort((a, b) => b.length - a.length)

      sortedTerms.forEach(term => {
        if (term && term.length > 2) {
          const regex = new RegExp(`(${term})`, 'gi')
          highlightedText = highlightedText.replace(
            regex,
            '<mark class="highlight-term">$1</mark>'
          )
        }
      })

      return highlightedText
    }

    onMounted(() => {
      // Додаємо обробник комбінації клавіш Ctrl + Enter
      document.addEventListener('keydown', handleCtrlEnter)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleCtrlEnter)
    })

    return {
      question,
      answer,
      contexts,
      evaluation,
      evaluationPending,
      loading,
      isStreaming,
      hasSearched,
      isFocused,
      showContexts,
      showEvaluation,
      validationFailed,
      validationReason,
      streamingStatus,
      responseTime,
      showGameInvitation,
      showDinoGame,
      currentProcessStage,
      easterEggsRef,
      placeholderText,
      formattedAnswer,
      metricsDisplay,
      overallQuality,
      handleSearch,
      getMetricColor,
      getMetricColorName,
      formatSourceName,
      getSourceIcon,
      getSourceColor,
      highlightKeyTerms,
      openDinoGame,
      closeDinoGame
    }
  }
})
</script>

<style lang="scss" scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.animated {
  animation-duration: 0.5s;
  animation-fill-mode: both;
}

.fadeIn {
  animation-name: fadeIn;
}

.fadeOut {
  animation-name: fadeOut;
}

.animated-header {
  animation: fadeIn 1s ease;
}

.typing-animation {
  animation: fadeIn 1.5s ease;
}

.search-icon-pulse {
  animation: pulse-scale 2s infinite;
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.hover-rotate {
  transition: transform 0.3s ease;
  &:hover {
    transform: rotate(90deg);
  }
}

.animated-toggle {
  transition: all 0.3s ease;
  &:hover {
    transform: scale(1.05);
  }
}

.glowing-button {
  position: relative;
  overflow: hidden;
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
  }
  &:hover::before {
    width: 300px;
    height: 300px;
  }
}

.card-hover {
  transition: all 0.3s ease;
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }
}

.icon-bounce {
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.icon-pulse {
  animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.badge-pulse {
  animation: badge-pulse 2s infinite;
}

@keyframes badge-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.streaming-chip {
  animation: glow 1.5s infinite;
}

@keyframes glow {
  0%, 100% { box-shadow: 0 0 5px rgba(25, 118, 210, 0.5); }
  50% { box-shadow: 0 0 20px rgba(25, 118, 210, 0.8); }
}

.counter-animation {
  animation: count-up 0.5s ease-out;
}

@keyframes count-up {
  from { transform: scale(0); }
  to { transform: scale(1); }
}

.bounce-in {
  animation: bounce-in 0.5s ease;
}

@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    transform: scale(1);
  }
}

.shake-animation {
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.shake-enter-active {
  animation: shake 0.5s ease;
}

.stagger-fade-enter-active {
  transition: all 0.5s ease;
}

.stagger-fade-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.stagger-fade-move {
  transition: transform 0.5s ease;
}

.streaming-text {
  position: relative;
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background-color: #1976D2;
  margin-left: 2px;
  animation: blink 1s infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.answer-content {
  font-size: 1.1rem;
  line-height: 1.8;
  color: #333;
  min-height: 60px;

  :deep(p) {
    margin-bottom: 1rem;
  }

  :deep(ul), :deep(ol) {
    margin-left: 1.5rem;
    margin-bottom: 1rem;
  }
}

:deep(.highlight-term) {
  background: linear-gradient(120deg, #fff59d 0%, #fdd835 100%);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  color: #000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;

  &:hover {
    background: linear-gradient(120deg, #fdd835 0%, #f9a825 100%);
    transform: scale(1.05);
  }
}

.validation-banner {
  border-left: 4px solid #F44336;
  animation: shake 0.5s ease;
}

.quality-banner {
  border-left: 4px solid;
  transition: all 0.3s ease;

  &.quality-excellent {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
    border-left-color: #4CAF50;
  }

  &.quality-good {
    background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.05) 100%);
    border-left-color: #2196F3;
  }

  &.quality-fair {
    background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(255, 152, 0, 0.05) 100%);
    border-left-color: #FF9800;
  }

  &.quality-low {
    background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%);
    border-left-color: #F44336;
  }
}

.gradient-text {
  background: linear-gradient(135deg, #1976D2 0%, #2196F3 50%, #64B5F6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 3s ease infinite;
  background-size: 200% 200%;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>
