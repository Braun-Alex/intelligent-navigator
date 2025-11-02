<template>
  <q-page class="flex flex-center bg-pattern">
    <div class="container q-pa-md">
      <div class="text-center q-mb-xl" v-if="!hasSearched">
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
        <p class="text-h6 text-grey-7">
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
                  @keyup.enter.ctrl="handleSearch"
                  class="search-input"
                  :input-style="{ minHeight: '56px' }"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" size="28px" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      round
                      dense
                      flat
                      icon="close"
                      v-if="question"
                      @click="question = ''"
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
                    />
                    <q-toggle
                      v-model="showEvaluation"
                      label="Оцінити якість відповіді"
                      color="secondary"
                      left-label
                      class="q-ml-md"
                    />
                  </div>

                  <div class="col-auto">
                    <q-btn
                      unelevated
                      rounded
                      color="primary"
                      label="Знайти відповідь"
                      icon="mdi-magnify"
                      size="lg"
                      @click="handleSearch"
                      :loading="loading"
                      :disable="!question.trim()"
                      class="search-button"
                    >
                      <template v-slot:loading>
                        <q-spinner-hourglass color="white" />
                      </template>
                    </q-btn>
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Посилання на нормативні документи КНУТШ -->
        <div class="q-mt-md" v-if="!hasSearched">
          <q-card flat bordered class="official-docs-card">
            <q-card-section class="row items-center q-py-md">
              <q-icon name="mdi-file-document-multiple" size="48px" color="primary" class="q-mr-md" />
              <div class="col">
                <div class="text-h6 text-weight-medium">Офіційні документи КНУТШ</div>
                <div class="text-caption text-grey-7">
                  Нормативні документи Київського національного університету імені Тараса Шевченка
                </div>
              </div>
              <q-btn
                unelevated
                rounded
                color="primary"
                label="Переглянути"
                icon-right="mdi-open-in-new"
                size="md"
                href="https://knu.ua/official"
                target="_blank"
                class="official-docs-button"
              >
                <q-tooltip>Відкрити офіційний сайт КНУТШ</q-tooltip>
              </q-btn>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Секція відповіді -->
      <transition
        appear
        enter-active-class="animated fadeIn"
        leave-active-class="animated fadeOut"
      >
        <div v-if="hasSearched && answer" class="results-container">
          <!-- Повідомлення про непроходження валідації системи -->
          <q-banner
            v-if="validationFailed"
            class="bg-negative text-white q-mb-md validation-banner"
            rounded
          >
            <template v-slot:avatar>
              <q-icon name="mdi-shield-alert" size="48px" />
            </template>
            <div class="text-h6 text-weight-bold">Запит відхилено</div>
            <div class="text-body1 q-mt-sm">{{ validationReason }}</div>
            <div class="text-caption q-mt-md">
              <q-icon name="mdi-information" class="q-mr-xs" />
              Будь ласка, переформулюйте запитання так, щоб воно стосувалося нормативних документів КНУТШ.
            </div>
          </q-banner>

          <!-- Відповідь системи -->
          <q-card flat bordered class="answer-card q-mb-md" v-if="!validationFailed">
            <q-card-section>
              <div class="row items-center q-mb-md">
                <q-icon name="mdi-comment-quote" size="32px" color="primary" class="q-mr-sm" />
                <span class="text-h5 text-weight-bold">Відповідь</span>
              </div>
              <div class="answer-content" v-html="formattedAnswer"></div>
            </q-card-section>

            <!-- Оцінка якості відповіді -->
            <q-card-section v-if="showEvaluation && evaluation" class="bg-blue-grey-1">
              <div class="text-subtitle1 text-weight-bold q-mb-sm">
                <q-icon name="mdi-chart-bar" class="q-mr-sm" />
                Оцінка якості відповіді
              </div>

              <!-- Інтерпретація оцінки якості відповіді -->
              <q-banner
                :class="`q-mb-md quality-banner quality-${overallQuality.level}`"
                rounded
              >
                <template v-slot:avatar>
                  <q-icon
                    :name="overallQuality.icon"
                    :color="overallQuality.color"
                    size="48px"
                  />
                </template>
                <div class="text-h6 text-weight-bold">{{ overallQuality.title }}</div>
                <div class="text-body2 q-mt-xs">{{ overallQuality.description }}</div>
              </q-banner>

              <div class="row q-col-gutter-md">
                <div class="col-6 col-md-4 col-lg-2" v-for="(metric, key) in metricsDisplay" :key="key">
                  <q-card flat class="metric-card">
                    <q-card-section class="text-center">
                      <div class="text-h4 text-weight-bold" :class="getMetricColor(metric.value)">
                        {{ (metric.value * 100).toFixed(0) }}%
                      </div>
                      <div class="text-caption text-weight-bold text-grey-8">{{ metric.label }}</div>
                      <div class="text-caption text-grey-6" style="font-size: 10px;">{{ metric.englishName }}</div>
                      <q-linear-progress
                        :value="metric.value"
                        :color="getMetricColorName(metric.value)"
                        size="8px"
                        rounded
                        class="q-mt-sm"
                      />
                      <q-tooltip class="bg-dark text-body2" max-width="250px">
                        <div class="text-weight-bold q-mb-xs">{{ metric.label }}</div>
                        <div>{{ metric.explanation }}</div>
                      </q-tooltip>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-card-section>
          </q-card>

          <!-- Контекст відповідей -->
          <q-card flat bordered class="contexts-card" v-if="showContexts && contexts.length > 0">
            <q-card-section>
              <div class="row items-center q-mb-lg">
                <q-icon name="mdi-file-document-multiple" size="32px" color="secondary" class="q-mr-sm" />
                <span class="text-h5 text-weight-bold">Знайдені джерела ({{ contexts.length }})</span>
              </div>

              <!-- Відображення джерел -->
              <div class="q-gutter-md">
                <q-card
                  v-for="(context, idx) in contexts"
                  :key="idx"
                  flat
                  bordered
                  class="source-card"
                >
                  <!-- Заголовок джерела -->
                  <q-card-section class="source-header bg-grey-2">
                    <div class="row items-center justify-between">
                      <div class="col">
                        <div class="row items-center q-gutter-sm">
                          <q-icon
                            :name="getSourceIcon(context.source || context.metadata?.source)"
                            size="24px"
                            :color="getSourceColor(idx)"
                          />
                          <div>
                            <div class="text-subtitle1 text-weight-bold">
                              {{ formatSourceName(context.source || context.metadata?.source) }}
                            </div>
                            <div class="text-caption text-grey-7" v-if="context.section || context.metadata?.section_title">
                              {{ context.section || context.metadata?.section_title }}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="col-auto">
                        <q-badge
                          :color="getSourceColor(idx)"
                          text-color="white"
                          :label="`${idx + 1}`"
                        />
                      </div>
                    </div>
                  </q-card-section>

                  <!-- Попередній перегляд джерела -->
                  <q-card-section>
                    <div
                      class="text-body2 text-grey-8 context-preview"
                      v-html="highlightKeyTerms(
                        context.preview || (context.content?.length > 300 ? context.content.substring(0, 300) + '...' : context.content),
                        context.key_terms || []
                      )"
                    >
                    </div>
                  </q-card-section>

                  <!-- Розгорнутий вміст джерела -->
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

                  <!-- Метадані -->
                  <q-card-section class="q-pt-none">
                    <q-separator class="q-mb-sm" />
                    <div class="row q-gutter-sm text-caption text-grey-7">
                      <q-chip
                        dense
                        square
                        icon="mdi-text-box"
                        size="sm"
                      >
                        {{ context.length || context.content?.length || 0 }} символів
                      </q-chip>
                      <q-chip
                        dense
                        square
                        icon="mdi-file-document"
                        size="sm"
                        v-if="context.chunk_index !== undefined && context.chunk_index !== null"
                      >
                        Фрагмент {{ context.chunk_index + 1 }}
                      </q-chip>
                      <q-chip
                        dense
                        square
                        :icon="context.is_relevant ? 'mdi-check-circle' : 'mdi-alert-circle'"
                        :color="context.is_relevant ? 'positive' : 'negative'"
                        text-color="white"
                        size="sm"
                        v-if="context.is_relevant !== undefined && context.is_relevant !== null"
                      >
                        {{ context.is_relevant ? 'Релевантний' : 'Нерелевантний' }}
                      </q-chip>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <!-- Кількість джерел посилань -->
              <q-banner dense class="bg-blue-1 text-primary q-mt-md" rounded>
                <template v-slot:avatar>
                  <q-icon name="mdi-information" size="sm" />
                </template>
                <span class="text-caption">
                  Відповідь сформована на основі {{ contexts.length }}
                  {{ contexts.length === 1 ? 'фрагмента' : 'фрагментів' }}
                  з нормативних документів КНУТШ
                </span>
              </q-banner>
            </q-card-section>
          </q-card>
        </div>
      </transition>
    </div>
  </q-page>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '@/api/axios'
import { marked } from 'marked'

export default defineComponent({
  name: 'IndexPage',

  setup() {
    const $q = useQuasar()
    const question = ref('')
    const answer = ref('')
    const contexts = ref([])
    const evaluation = ref(null)
    const loading = ref(false)
    const hasSearched = ref(false)
    const isFocused = ref(false)
    const showContexts = ref(true)
    const showEvaluation = ref(true)
    const validationFailed = ref(false)
    const validationReason = ref('')

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
          englishName: 'Faithfulness',
          value: evaluation.value.faithfulness,
          explanation: 'Наскільки відповідь підтверджується джерелами. Висока достовірність означає, що всі твердження у відповіді базуються на наданих документах.'
        },
        answer_relevancy: {
          label: 'Релевантність відповіді',
          englishName: 'Answer Relevancy',
          value: evaluation.value.answer_relevancy,
          explanation: 'Наскільки відповідь відповідає на поставлене питання. Висока релевантність означає, що відповідь точно адресує запит користувача.'
        },
        context_relevancy: {
          label: 'Релевантність контексту',
          englishName: 'Context Relevancy',
          value: evaluation.value.context_relevancy,
          explanation: 'Наскільки знайдені фрагменти документів стосуються запитання. Висока оцінка означає, що система знайшла правильні розділи.'
        },
        mrr: {
          label: 'MRR',
          englishName: 'Mean Reciprocal Rank',
          value: evaluation.value.mrr,
          explanation: 'Mean Reciprocal Rank - оцінює позицію першого релевантного документа.'
        },
        map: {
          label: 'MAP',
          englishName: 'Mean Average Precision',
          value: evaluation.value.map,
          explanation: 'Mean Average Precision - середня точність пошуку. Враховує позиції всіх релевантних документів.'
        },
        overall_score: {
          label: 'Загальна оцінка',
          englishName: 'Overall Score',
          value: evaluation.value.overall_score,
          explanation: 'Комплексна оцінка якості відповіді на основі всіх метрик. Показує загальну надійність отриманої інформації.'
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

    const handleSearch = async () => {
      if (!question.value.trim()) {
        $q.notify({
          type: 'warning',
          message: 'Будь ласка, введіть запитання',
          position: 'top'
        })
        return
      }

      loading.value = true
      hasSearched.value = true
      answer.value = ''
      contexts.value = []
      evaluation.value = null
      validationFailed.value = false
      validationReason.value = ''

      try {
        const response = await api.post('/query', {
          question: question.value,
          return_contexts: showContexts.value,
          return_evaluation: showEvaluation.value
        })

        answer.value = response.data.answer

        // Перевірка валідації
        if (response.data.validation_failed) {
          validationFailed.value = true
          validationReason.value = response.data.validation_reason || response.data.answer
          $q.notify({
            type: 'warning',
            message: 'Запит відхилено системою валідації',
            position: 'top',
            icon: 'mdi-shield-alert',
            timeout: 4000
          })
          return
        }

        if (response.data.contexts) {
          contexts.value = response.data.contexts
        }

        if (response.data.evaluation) {
          evaluation.value = response.data.evaluation
        }

        $q.notify({
          type: 'positive',
          message: 'Відповідь отримано успішно!',
          position: 'top',
          icon: 'mdi-check-circle'
        })
      } catch (error) {
        console.error('Помилка пошуку:', error)
        $q.notify({
          type: 'negative',
          message: 'Помилка при отриманні відповіді: ' + (error.response?.data?.detail || error.message),
          position: 'top',
          timeout: 5000
        })
      } finally {
        loading.value = false
      }
    }

    // Форматування назви документа
    const formatSourceName = (source) => {
      if (!source) return 'Невідоме джерело'

      let name = source.replace('.pdf', '')
      name = name.replace(/-/g, ' ')
      name = name.replace(/_/g, ' ')

      if (name.length > 60) {
        name = name.substring(0, 57) + '...'
      }

      return name
    }

    // Іконка для джерела
    const getSourceIcon = (source) => {
      if (!source) return 'mdi-file-document'

      const sourceLower = source.toLowerCase()

      if (sourceLower.includes('polozhennia') || sourceLower.includes('положення')) {
        return 'mdi-book-open-variant'
      }
      if (sourceLower.includes('regulation') || sourceLower.includes('регламент')) {
        return 'mdi-file-certificate'
      }
      if (sourceLower.includes('integrity') || sourceLower.includes('доброчесн')) {
        return 'mdi-shield-check'
      }

      return 'mdi-file-document-outline'
    }

    // Колір для джерела
    const getSourceColor = (idx) => {
      const colors = ['primary', 'secondary', 'accent', 'positive', 'info']
      return colors[idx % colors.length]
    }

    // Підсвітка ключових термінів у тексті
    const highlightKeyTerms = (text, keyTerms) => {
      if (!text || !keyTerms || keyTerms.length === 0) {
        return text
      }

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

    return {
      question,
      answer,
      contexts,
      evaluation,
      loading,
      hasSearched,
      isFocused,
      showContexts,
      showEvaluation,
      validationFailed,
      validationReason,
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
      highlightKeyTerms
    }
  }
})
</script>

<style lang="scss" scoped>
.bg-pattern {
  background:
    radial-gradient(circle at 20% 50%, rgba(25, 118, 210, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(156, 39, 176, 0.1) 0%, transparent 50%);
}

.container {
  width: 100%;
  max-width: 1200px;
}

.gradient-text {
  background: linear-gradient(135deg, #1976D2 0%, #9C27B0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.icon-wrapper {
  display: inline-block;
  position: relative;
}

.animated-icon {
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 4px 12px rgba(25, 118, 210, 0.4));
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(5deg);
  }
}

.search-card {
  transition: all 0.3s ease;
  border-radius: 16px;
}

.elevated-card {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.search-input {
  font-size: 1.1rem;
}

.search-button {
  padding: 12px 32px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.official-docs-card {
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.02) 0%, rgba(156, 39, 176, 0.02) 100%);
  border: 2px solid rgba(25, 118, 210, 0.1);
  transition: all 0.3s ease;
}

.official-docs-card:hover {
  border-color: rgba(25, 118, 210, 0.3);
  box-shadow: 0 4px 20px rgba(25, 118, 210, 0.1);
  transform: translateY(-2px);
}

.official-docs-button {
  padding: 10px 24px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.info-chip {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.info-chip:hover {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.answer-card,
.contexts-card {
  border-radius: 16px;
  overflow: hidden;
}

.source-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.source-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.source-header {
  border-bottom: 1px solid #e0e0e0;
}

.context-preview {
  line-height: 1.6;
  text-align: justify;
}

:deep(.highlight-term) {
  background-color: #fff59d;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
  color: #000;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.answer-content {
  font-size: 1.1rem;
  line-height: 1.8;
  color: #333;

  :deep(p) {
    margin-bottom: 1rem;
  }

  :deep(ul), :deep(ol) {
    margin-left: 1.5rem;
    margin-bottom: 1rem;
  }
}

.metric-card {
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.context-content {
  background: rgba(0, 0, 0, 0.02);
  padding: 12px;
  border-radius: 8px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.quality-banner {
  border-left: 4px solid;

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

.validation-banner {
  border-left: 4px solid #F44336;
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}
</style>
