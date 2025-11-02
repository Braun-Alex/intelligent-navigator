<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row items-center q-mb-lg">
        <q-icon name="mdi-chart-line" size="48px" color="primary" class="q-mr-md" />
        <div>
          <h1 class="text-h4 text-weight-bold q-ma-none">Аналітика RAG</h1>
          <p class="text-subtitle1 text-grey-7 q-ma-none">Оцінка якості та продуктивності системи</p>
        </div>
      </div>

      <q-card flat bordered class="q-mb-md">
        <q-card-section>
          <div class="row items-center justify-between">
            <div class="text-h6">Оцінка якості відповідей</div>
            <q-btn
              outline
              color="primary"
              label="Оновити"
              icon="mdi-refresh"
              @click="loadReport"
              :loading="loading"
            />
          </div>
        </q-card-section>
      </q-card>

      <div v-if="loading" class="text-center q-pa-xl">
        <q-spinner-dots color="primary" size="50px" />
        <div class="text-subtitle1 q-mt-md">Завантаження аналітики...</div>
      </div>

      <div v-else-if="report">
        <!-- Загальна інформація -->
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-12 col-md-3">
            <q-card flat bordered class="stat-card">
              <q-card-section>
                <div class="text-h3 text-weight-bold text-primary">
                  {{ report.total_evaluations || 0 }}
                </div>
                <div class="text-subtitle2 text-grey-7">Всього оцінок</div>
              </q-card-section>
            </q-card>
          </div>

          <div class="col-12 col-md-3">
            <q-card flat bordered class="stat-card">
              <q-card-section>
                <div class="text-h3 text-weight-bold text-positive">
                  {{ formatPercent(avgMetrics.avg_overall_score) }}
                </div>
                <div class="text-subtitle2 text-grey-7">Середній бал</div>
              </q-card-section>
            </q-card>
          </div>

          <div class="col-12 col-md-3">
            <q-card flat bordered class="stat-card">
              <q-card-section>
                <div class="text-h3 text-weight-bold text-secondary">
                  {{ formatPercent(avgMetrics.avg_faithfulness) }}
                </div>
                <div class="text-subtitle2 text-grey-7">Достовірність</div>
              </q-card-section>
            </q-card>
          </div>

          <div class="col-12 col-md-3">
            <q-card flat bordered class="stat-card">
              <q-card-section>
                <div class="text-h3 text-weight-bold" :class="getTrendColor(report.trend?.trend)">
                  <q-icon :name="getTrendIcon(report.trend?.trend)" size="32px" />
                </div>
                <div class="text-subtitle2 text-grey-7">Тренд: {{ getTrendLabel(report.trend?.trend) }}</div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- Детальна оцінка якості -->
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="text-h6 q-mb-md">Детальні метрики</div>
            
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6" v-for="metric in detailedMetrics" :key="metric.key">
                <div class="metric-item">
                  <div class="row items-center justify-between q-mb-xs">
                    <div>
                      <div class="text-subtitle1 text-weight-bold">{{ metric.label }}</div>
                      <div class="text-caption text-grey-6">{{ metric.englishName }}</div>
                    </div>
                    <div class="text-h6 text-weight-bold" :class="getMetricTextColor(metric.avg)">
                      {{ formatPercent(metric.avg) }}
                    </div>
                  </div>
                  <div class="text-caption text-grey-7 q-mb-sm">
                    {{ metric.explanation }}
                  </div>
                  <q-linear-progress
                    :value="metric.avg"
                    :color="getMetricColor(metric.avg)"
                    size="12px"
                    rounded
                    class="q-mb-xs"
                  />
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Дані про останню оцінку якості -->
        <q-card flat bordered v-if="report.latest_evaluation">
          <q-card-section>
            <div class="text-h6 q-mb-md">Остання оцінка</div>
            
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <div class="text-subtitle2 text-grey-7">Запит:</div>
                <div class="text-body1 q-mb-md">{{ report.latest_evaluation.query }}</div>
                
                <div class="text-subtitle2 text-grey-7">Відповідь:</div>
                <div class="text-body2">{{ report.latest_evaluation.answer }}</div>
              </div>

              <div class="col-12 col-md-6">
                <div class="text-subtitle2 text-grey-7 q-mb-sm">Оцінки:</div>
                <q-list bordered separator>
                  <q-item>
                    <q-item-section>Достовірність</q-item-section>
                    <q-item-section side>
                      <q-badge :color="getMetricColor(report.latest_evaluation.faithfulness)">
                        {{ formatPercent(report.latest_evaluation.faithfulness) }}
                      </q-badge>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>Релевантність відповіді</q-item-section>
                    <q-item-section side>
                      <q-badge :color="getMetricColor(report.latest_evaluation.answer_relevancy)">
                        {{ formatPercent(report.latest_evaluation.answer_relevancy) }}
                      </q-badge>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>Релевантність контексту</q-item-section>
                    <q-item-section side>
                      <q-badge :color="getMetricColor(report.latest_evaluation.relevancy)">
                        {{ formatPercent(report.latest_evaluation.relevancy) }}
                      </q-badge>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>MRR</q-item-section>
                    <q-item-section side>
                      <q-badge :color="getMetricColor(report.latest_evaluation.mrr)">
                        {{ formatPercent(report.latest_evaluation.mrr) }}
                      </q-badge>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>MAP</q-item-section>
                    <q-item-section side>
                      <q-badge :color="getMetricColor(report.latest_evaluation.map_score)">
                        {{ formatPercent(report.latest_evaluation.map_score) }}
                      </q-badge>
                    </q-item-section>
                  </q-item>
                  <q-item>
                    <q-item-section>Загальна оцінка</q-item-section>
                    <q-item-section side>
                      <q-badge :color="getMetricColor(report.latest_evaluation.overall_score)">
                        {{ formatPercent(report.latest_evaluation.overall_score) }}
                      </q-badge>
                    </q-item-section>
                  </q-item>
                </q-list>

                <div class="text-caption text-grey-7 q-mt-sm">
                  Час: {{ formatDate(report.latest_evaluation.timestamp) }}
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div v-else class="text-center q-pa-xl">
        <q-icon name="mdi-information" size="64px" color="grey-5" />
        <div class="text-h6 text-grey-7 q-mt-md">Немає даних для відображення</div>
        <div class="text-body2 text-grey-6">Виконайте кілька запитів з увімкненими метриками</div>
      </div>
    </div>
  </q-page>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '@/api/axios'

export default defineComponent({
  name: 'AnalyticsPage',

  setup() {
    const $q = useQuasar()
    const loading = ref(false)
    const report = ref(null)

    const avgMetrics = computed(() => {
      return report.value?.average_metrics || {}
    })

    const detailedMetrics = computed(() => {
      if (!report.value?.average_metrics) return []
      
      const metrics = report.value.average_metrics
      return [
        { 
          key: 'faithfulness', 
          label: 'Достовірність', 
          englishName: 'Faithfulness',
          explanation: 'Показує, наскільки відповіді підтверджуються джерелами.',
          avg: metrics.avg_faithfulness || 0
        },
        { 
          key: 'answer_relevancy', 
          label: 'Релевантність відповіді', 
          englishName: 'Answer Relevancy',
          explanation: 'Вимірює, наскільки відповіді точно адресують запити користувачів.',
          avg: metrics.avg_answer_relevancy || 0
        },
        { 
          key: 'context_relevancy', 
          label: 'Релевантність контексту', 
          englishName: 'Context Relevancy',
          explanation: 'Оцінює, наскільки знайдені фрагменти документів стосуються запитань.',
          avg: metrics.avg_relevancy || 0
        },
        { 
          key: 'mrr', 
          label: 'MRR', 
          englishName: 'Mean Reciprocal Rank',
          explanation: 'Оцінює позицію першого релевантного документа.',
          avg: metrics.avg_mrr || 0
        },
        { 
          key: 'map', 
          label: 'MAP', 
          englishName: 'Mean Average Precision',
          explanation: 'Середня точність пошуку. Враховує позиції всіх релевантних документів.',
          avg: metrics.avg_map || 0
        }
      ]
    })

    const getMetricTextColor = (value) => {
      if (value >= 0.8) return 'text-positive'
      if (value >= 0.6) return 'text-warning'
      return 'text-negative'
    }

    const formatPercent = (value) => {
      if (value === undefined || value === null) return 'N/A'
      return `${(value * 100).toFixed(1)}%`
    }

    const formatDate = (timestamp) => {
      if (!timestamp) return 'N/A'
      const date = new Date(timestamp)
      return date.toLocaleString('uk-UA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
      })
    }

    const getMetricColor = (value) => {
      if (value >= 0.8) return 'positive'
      if (value >= 0.6) return 'warning'
      return 'negative'
    }

    const getTrendColor = (trend) => {
      if (trend === 'improving') return 'text-positive'
      if (trend === 'declining') return 'text-negative'
      return 'text-grey-7'
    }

    const getTrendIcon = (trend) => {
      if (trend === 'improving') return 'mdi-trending-up'
      if (trend === 'declining') return 'mdi-trending-down'
      return 'mdi-trending-neutral'
    }

    const getTrendLabel = (trend) => {
      if (trend === 'improving') return 'Покращення'
      if (trend === 'declining') return 'Погіршення'
      if (trend === 'stable') return 'Стабільно'
      return 'Недостатньо даних'
    }

    const loadReport = async () => {
      loading.value = true
      try {
        const response = await api.get('/evaluation/report')
        report.value = response.data
      } catch (error) {
        console.error('Не вдалося завантажити звіт оцінки якості:', error)
        $q.notify({
          type: 'negative',
          message: 'Помилка завантаження звіту оцінки якості',
          position: 'top'
        })
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadReport()
    })

    return {
      loading,
      report,
      avgMetrics,
      detailedMetrics,
      formatPercent,
      formatDate,
      getMetricColor,
      getMetricTextColor,
      getTrendColor,
      getTrendIcon,
      getTrendLabel,
      loadReport
    }
  }
})
</script>

<style lang="scss" scoped>
.stat-card {
  border-radius: 12px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }
}

.metric-item {
  padding: 16px;
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.02) 0%, rgba(156, 39, 176, 0.02) 100%);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  transition: all 0.3s ease;
  
  &:hover {
    background: linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(156, 39, 176, 0.05) 100%);
    border-color: rgba(25, 118, 210, 0.2);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
  }
}
</style>
