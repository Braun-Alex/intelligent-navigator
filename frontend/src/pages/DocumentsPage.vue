<template>
  <q-page padding>
    <div class="q-pa-md">
      <div class="row items-center q-mb-lg">
        <q-icon name="mdi-file-document-multiple" size="48px" color="primary" class="q-mr-md" />
        <div>
          <h1 class="text-h4 text-weight-bold q-ma-none">Документи</h1>
          <p class="text-subtitle1 text-grey-7 q-ma-none">Джерела знань системи RAG</p>
        </div>
      </div>

      <div v-if="loading" class="text-center q-pa-xl">
        <q-spinner-dots color="primary" size="50px" />
        <div class="text-subtitle1 q-mt-md">Завантаження документів...</div>
      </div>

      <div v-else>
        <q-card flat bordered class="q-mb-md">
          <q-card-section>
            <div class="row items-center justify-between q-mb-md">
              <div>
                <div class="text-h6">Всього документів: {{ documents.length }}</div>
                <div class="text-caption text-grey-7 q-mt-xs">
                  Проіндексовано чанків: {{ vectorStoreSize >= 0 ? vectorStoreSize : '?' }}
                </div>
              </div>
              <q-btn
                outline
                color="primary"
                label="Оновити"
                icon="mdi-refresh"
                @click="loadDocuments"
              />
            </div>
            
            <div class="row q-gutter-sm">
              <q-btn
                unelevated
                color="positive"
                label="Індексувати документи"
                icon="mdi-database-import"
                @click="indexDocuments"
                :loading="indexing"
                :disable="indexing || resetting"
              >
                <q-tooltip>Додає документи до сховища</q-tooltip>
              </q-btn>
              
              <q-btn
                unelevated
                color="warning"
                label="Переіндексувати"
                icon="mdi-database-refresh"
                @click="confirmReset"
                :loading="resetting"
                :disable="indexing || resetting"
              >
                <q-tooltip>Очищає сховище і повторно його індексує</q-tooltip>
              </q-btn>
            </div>
          </q-card-section>
        </q-card>

        <div class="row q-col-gutter-md">
          <div class="col-12 col-md-6" v-for="doc in documents" :key="doc.filename">
            <q-card flat bordered class="document-card">
              <q-card-section>
                <div class="row items-start">
                  <q-icon name="mdi-file-pdf-box" size="48px" color="red" class="q-mr-md" />
                  <div class="col">
                    <div class="text-h6 text-weight-bold q-mb-xs">
                      {{ formatFilename(doc.filename) }}
                    </div>
                    <div class="text-caption text-grey-7">
                      {{ doc.filename }}
                    </div>
                    <div class="q-mt-sm">
                      <q-chip
                        v-if="doc.file_size"
                        size="sm"
                        color="blue-grey-2"
                        text-color="blue-grey-8"
                        icon="mdi-file"
                      >
                        {{ formatFileSize(doc.file_size) }}
                      </q-chip>
                      <q-chip
                        v-if="doc.total_pages"
                        size="sm"
                        color="blue-grey-2"
                        text-color="blue-grey-8"
                        icon="mdi-book-open-page-variant"
                      >
                        {{ doc.total_pages }} сторінок
                      </q-chip>
                    </div>
                  </div>
                </div>
              </q-card-section>

              <q-separator />

              <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Про документ:</div>
                <div class="text-body2 text-grey-7">
                  {{ getDocumentDescription(doc.filename) }}
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <div v-if="documents.length === 0" class="text-center q-pa-xl">
          <q-icon name="mdi-file-question" size="64px" color="grey-5" />
          <div class="text-h6 text-grey-7 q-mt-md">Документи не знайдено</div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '@/api/axios'

export default defineComponent({
  name: 'DocumentsPage',

  setup() {
    const $q = useQuasar()
    const loading = ref(false)
    const indexing = ref(false)
    const resetting = ref(false)
    const documents = ref([])
    const vectorStoreSize = ref(-1)

    const loadDocuments = async () => {
      loading.value = true
      try {
        const response = await api.get('/documents')
        documents.value = response.data.documents || []

        const healthResponse = await api.get('/health')
        vectorStoreSize.value = healthResponse.data.vector_store_size || 0
      } catch (error) {
        console.error('Не вдалося завантажити документи:', error)
        $q.notify({
          type: 'negative',
          message: 'Помилка завантаження документів',
          position: 'top'
        })
      } finally {
        loading.value = false
      }
    }

    const indexDocuments = async () => {
      indexing.value = true
      try {
        $q.notify({
          type: 'info',
          message: 'Початок індексації документів...',
          position: 'top'
        })
        
        const response = await api.post('/index')
        
        $q.notify({
          type: 'positive',
          message: `Індексацію завершено! Додано ${response.data.documents_added} чанків`,
          position: 'top',
          timeout: 5000
        })

        await loadDocuments()
      } catch (error) {
        console.error('Помилка індексації:', error)
        $q.notify({
          type: 'negative',
          message: error.response?.data?.detail || 'Помилка індексації документів',
          position: 'top'
        })
      } finally {
        indexing.value = false
      }
    }

    const confirmReset = () => {
      $q.dialog({
        title: 'Підтвердження',
        message: 'Ви є впевненими, що хочете очистити векторне сховище і переіндексувати всі документи? Це може тривати кілька хвилин.',
        cancel: {
          label: 'Скасувати',
          color: 'grey',
          flat: true
        },
        ok: {
          label: 'Так, переіндексувати',
          color: 'warning'
        }
      }).onOk(async () => {
        await resetVectorStore()
      })
    }

    const resetVectorStore = async () => {
      resetting.value = true
      try {
        $q.notify({
          type: 'info',
          message: 'Початок переіндексації...',
          position: 'top'
        })
        
        await api.post('/reset')
        
        $q.notify({
          type: 'positive',
          message: 'Векторне сховище успішно переіндексовано!',
          position: 'top',
          timeout: 5000
        })

        await loadDocuments()
      } catch (error) {
        console.error('Помилка переіндексації:', error)
        $q.notify({
          type: 'negative',
          message: error.response?.data?.detail || 'Помилка переіндексації',
          position: 'top'
        })
      } finally {
        resetting.value = false
      }
    }

    const formatFilename = (filename) => {
      return filename
        .replace('.pdf', '')
        .replace(/-/g, ' ')
        .replace(/_/g, ' ')
    }

    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    const getDocumentDescription = (filename) => {
      if (filename.includes('academic-integrity') || filename.includes('dobrochesnost')) {
        return 'Положення про забезпечення дотримання академічної доброчесності в Київському національному університеті імені Тараса Шевченка'
      }
      if (filename.includes('organizatsiyu-osvitniogo') || filename.includes('educational')) {
        return 'Положення про організацію освітнього процесу в Київському національному університеті імені Тараса Шевченка'
      }
      return 'Нормативний документ Київського національного університету імені Тараса Шевченка'
    }

    onMounted(() => {
      loadDocuments()
    })

    return {
      loading,
      indexing,
      resetting,
      documents,
      vectorStoreSize,
      loadDocuments,
      indexDocuments,
      confirmReset,
      formatFilename,
      formatFileSize,
      getDocumentDescription
    }
  }
})
</script>

<style lang="scss" scoped>
.document-card {
  border-radius: 12px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }
}
</style>
