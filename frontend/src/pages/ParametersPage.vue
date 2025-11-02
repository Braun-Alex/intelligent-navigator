<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row items-center q-mb-lg">
        <q-icon name="mdi-tune" size="48px" color="primary" class="q-mr-md" />
        <div>
          <h1 class="text-h4 text-weight-bold q-ma-none">Параметри системи</h1>
          <p class="text-subtitle1 text-grey-7 q-ma-none">Налаштування параметрів RAG</p>
        </div>
      </div>

      <!-- Вкладки -->
      <q-tabs
        v-model="tab"
        dense
        class="text-grey-8 q-mb-md"
        active-color="primary"
        indicator-color="primary"
        align="left"
      >
        <q-tab name="current" label="Поточні параметри" icon="mdi-eye" />
        <q-tab name="manual" label="Ручне налаштування" icon="mdi-pencil" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="tab" animated>
        <!-- Поточні параметри -->
        <q-tab-panel name="current">
          <div class="row items-center justify-between q-mb-md">
            <div class="text-h6">Поточна конфігурація</div>
            <q-btn
              outline
              color="primary"
              label="Оновити"
              icon="mdi-refresh"
              @click="loadCurrentParameters"
              :loading="loading"
            />
          </div>

          <div v-if="currentParams" class="row q-col-gutter-md">
            <div class="col-12 col-md-6" v-for="param in parametersList" :key="param.key">
              <q-card flat bordered class="param-card">
                <q-card-section>
                  <div class="row items-center justify-between">
                    <div>
                      <div class="text-subtitle1 text-weight-bold">{{ param.label }}</div>
                      <div class="text-caption text-grey-6">{{ param.description }}</div>
                    </div>
                    <div class="text-h5 text-weight-bold text-primary">
                      {{ formatValue(currentParams[param.key], param.type) }}
                    </div>
                  </div>
                  <q-linear-progress
                    v-if="param.type === 'number'"
                    :value="normalizeValue(currentParams[param.key], param.min, param.max)"
                    color="primary"
                    size="8px"
                    rounded
                    class="q-mt-sm"
                  />
                </q-card-section>
              </q-card>
            </div>
          </div>

          <q-banner v-else class="bg-grey-2 q-mt-md" rounded>
            <template v-slot:avatar>
              <q-icon name="mdi-information" color="grey-7" />
            </template>
            <div class="text-body1">Завантаження параметрів...</div>
          </q-banner>
        </q-tab-panel>

        <!-- Ручне налаштування -->
        <q-tab-panel name="manual">
          <div class="text-h6 q-mb-md">Налаштування параметрів</div>

          <q-form @submit="saveParameters" class="q-gutter-md">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6" v-for="param in editableParameters" :key="param.key">
                <q-card flat bordered>
                  <q-card-section>
                    <div class="text-subtitle1 text-weight-bold q-mb-xs">
                      <q-icon :name="param.icon" class="q-mr-sm" />
                      {{ param.label }}
                    </div>
                    <div class="text-caption text-grey-6 q-mb-md">{{ param.description }}</div>

                    <q-slider
                      v-if="param.type === 'slider'"
                      v-model="editedParams[param.key]"
                      :min="param.min"
                      :max="param.max"
                      :step="param.step"
                      :label-value="`${editedParams[param.key]}${param.suffix || ''}`"
                      label-always
                      color="primary"
                      class="q-mt-md"
                    />

                    <q-slider
                      v-else-if="param.type === 'decimal'"
                      v-model="editedParams[param.key]"
                      :min="param.min"
                      :max="param.max"
                      :step="param.step"
                      :label-value="editedParams[param.key].toFixed(param.decimals || 2)"
                      label-always
                      color="secondary"
                      class="q-mt-md"
                    />

                    <div class="text-caption text-grey-7 q-mt-sm">
                      Рекомендовано: {{ param.recommended }}
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>

            <div class="row justify-end q-mt-lg">
              <q-btn
                outline
                color="grey-7"
                label="Скинути"
                icon="mdi-restore"
                @click="resetToDefault"
                class="q-mr-sm"
              />
              <q-btn
                unelevated
                color="primary"
                label="Застосувати зміни"
                icon="mdi-check"
                type="submit"
                :loading="saving"
              />
            </div>
          </q-form>
        </q-tab-panel>
      </q-tab-panels>
    </div>
  </q-page>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '@/api/axios'

export default defineComponent({
  name: 'ParametersPage',

  setup() {
    const $q = useQuasar()
    const tab = ref('current')
    const loading = ref(false)
    const saving = ref(false)
    const currentParams = ref(null)
    const editedParams = ref({})

    const parametersList = computed(() => [
      { key: 'chunk_size', label: 'Розмір чанку', description: 'Розмір фрагментів тексту', type: 'number', min: 128, max: 2048 },
      { key: 'chunk_overlap', label: 'Перетин чанків', description: 'Перекриття між фрагментами', type: 'number', min: 32, max: 512 },
      { key: 'top_k', label: 'Top-K документів', description: 'Кількість документів для пошуку', type: 'number', min: 1, max: 20 },
      { key: 'rerank_top_k', label: 'Top-K після переранжування', description: 'Кількість після переранжування', type: 'number', min: 1, max: 15 },
      { key: 'bm25_weight', label: 'Вага BM25', description: 'Вага keyword пошуку', type: 'decimal', min: 0, max: 1 },
      { key: 'vector_weight', label: 'Вага векторного пошуку', description: 'Вага семантичного пошуку', type: 'decimal', min: 0, max: 1 }
    ])

    const editableParameters = computed(() => [
      {
        key: 'chunk_size',
        label: 'Розмір чанку',
        description: 'Розмір фрагментів тексту для індексації',
        icon: 'mdi-scissors-cutting',
        type: 'slider',
        min: 128,
        max: 2048,
        step: 128,
        recommended: '512-768',
        suffix: ' символів'
      },
      {
        key: 'chunk_overlap',
        label: 'Перетин чанків',
        description: 'Перекриття між сусідніми фрагментами',
        icon: 'mdi-set-merge',
        type: 'slider',
        min: 32,
        max: 512,
        step: 32,
        recommended: '128-192',
        suffix: ' символів'
      },
      {
        key: 'top_k',
        label: 'Кількість документів (Top-K)',
        description: 'Скільки документів отримувати зі сховища',
        icon: 'mdi-file-multiple',
        type: 'slider',
        min: 1,
        max: 20,
        step: 1,
        recommended: '5-7'
      },
      {
        key: 'rerank_top_k',
        label: 'Top-K після переранжування',
        description: 'Скільки документів залишити після переранжування',
        icon: 'mdi-sort-variant',
        type: 'slider',
        min: 1,
        max: 15,
        step: 1,
        recommended: '3-5'
      },
      {
        key: 'bm25_weight',
        label: 'Вага BM25-пошуку',
        description: 'Вага keyword-based пошуку в гібридній моделі',
        icon: 'mdi-text-search',
        type: 'decimal',
        min: 0.0,
        max: 1.0,
        step: 0.1,
        decimals: 1,
        recommended: '0.3-0.4'
      },
      {
        key: 'vector_weight',
        label: 'Вага векторного пошуку',
        description: 'Вага семантичного пошуку в гібридній моделі',
        icon: 'mdi-vector-combine',
        type: 'decimal',
        min: 0.0,
        max: 1.0,
        step: 0.1,
        decimals: 1,
        recommended: '0.6-0.7'
      },
    ])

    const formatValue = (value, type) => {
      if (value === undefined || value === null) return 'N/A'
      if (type === 'decimal') return value.toFixed(2)
      return value
    }

    const normalizeValue = (value, min, max) => {
      if (!value || !min || !max) return 0
      return (value - min) / (max - min)
    }

    const loadCurrentParameters = async () => {
      loading.value = true
      try {
        const response = await api.get('/parameters')
        currentParams.value = response.data
        editedParams.value = { ...response.data }
      } catch (error) {
        console.error('Помилка завантаження параметрів RAG:', error)
        $q.notify({
          type: 'negative',
          message: 'Не вдалося завантажити параметри RAG',
          position: 'top'
        })
      } finally {
        loading.value = false
      }
    }

    const saveParameters = async () => {
      saving.value = true
      try {
        await api.post('/parameters', editedParams.value)
        currentParams.value = { ...editedParams.value }

        $q.notify({
          type: 'positive',
          message: 'Параметри RAG успішно оновлено!',
          position: 'top',
          icon: 'mdi-check-circle'
        })

        tab.value = 'current'
      } catch (error) {
        console.error('Помилка збереження параметрів RAG:', error)
        $q.notify({
          type: 'negative',
          message: 'Помилка при збереженні параметрів RAG: ' + (error.response?.data?.detail || error.message),
          position: 'top'
        })
      } finally {
        saving.value = false
      }
    }

    const resetToDefault = () => {
      editedParams.value = {
        chunk_size: 512,
        chunk_overlap: 128,
        top_k: 5,
        rerank_top_k: 5,
        bm25_weight: 0.3,
        vector_weight: 0.7
      }

      $q.notify({
        type: 'info',
        message: 'Параметри RAG скинуто до типових значень',
        position: 'top'
      })
    }

    onMounted(() => {
      loadCurrentParameters()
    })

    return {
      tab,
      loading,
      saving,
      currentParams,
      editedParams,
      parametersList,
      editableParameters,
      formatValue,
      normalizeValue,
      loadCurrentParameters,
      saveParameters,
      resetToDefault
    }
  }
})
</script>

<style lang="scss" scoped>
.param-card {
  border-radius: 12px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}
</style>
