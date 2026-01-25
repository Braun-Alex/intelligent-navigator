<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-gradient-primary text-white">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
          class="q-mr-sm"
        />

        <q-toolbar-title class="text-weight-bold">
          <div class="row items-center">
            <q-icon name="school" size="32px" class="q-mr-sm" />
            <div>
              <div class="text-h6">Навігатор з документів КНУТШ</div>
              <div class="text-caption text-grey-3">Краще дізнатися зараз, ніж ніколи</div>
            </div>
          </div>
        </q-toolbar-title>

        <q-space />

        <q-chip
          v-if="stats.vector_store_size"
          outline
          color="white"
          text-color="white"
          icon="analytics"
          class="q-mr-sm"
        >
          {{ stats.vector_store_size }} фрагментів
        </q-chip>

        <q-btn
          flat
          round
          dense
          :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'"
          @click="$q.dark.toggle()"
        >
          <q-tooltip>Перемкнути тему</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      :width="280"
      :breakpoint="500"
      class="bg-drawer"
    >
      <q-scroll-area class="fit">
        <div class="q-pa-md">
          <div class="text-h6 text-weight-bold q-mb-md">
            <q-icon name="mdi-navigation" class="q-mr-sm" />
            Навігація
          </div>

          <q-list padding>
            <q-item
              clickable
              v-ripple
              to="/"
              exact
              active-class="bg-primary text-white"
              class="rounded-borders q-mb-sm"
            >
              <q-item-section avatar>
                <q-icon name="search" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Пошук</q-item-label>
                <q-item-label caption>Знайти інформацію</q-item-label>
              </q-item-section>
            </q-item>

            <q-item
              clickable
              v-ripple
              to="/analytics"
              active-class="bg-primary text-white"
              class="rounded-borders q-mb-sm"
            >
              <q-item-section avatar>
                <q-icon name="mdi-chart-line" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Аналітика</q-item-label>
                <q-item-label caption>Оцінка якості</q-item-label>
              </q-item-section>
            </q-item>

            <q-item
              clickable
              v-ripple
              to="/parameters"
              active-class="bg-primary text-white"
              class="rounded-borders q-mb-sm"
            >
              <q-item-section avatar>
                <q-icon name="mdi-tune" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Параметри</q-item-label>
                <q-item-label caption>Налаштування системи</q-item-label>
              </q-item-section>
            </q-item>

            <q-item
              clickable
              v-ripple
              to="/documents"
              active-class="bg-primary text-white"
              class="rounded-borders"
            >
              <q-item-section avatar>
                <q-icon name="mdi-file-document-multiple" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Документи</q-item-label>
                <q-item-label caption>Перегляд джерел</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>

          <q-separator class="q-my-md" />

          <div class="system-info-card q-pa-md rounded-borders">
            <div class="row items-center q-mb-md">
              <q-icon name="mdi-information" size="32px" color="white" class="q-mr-sm" />
              <div class="text-subtitle1 text-weight-bold text-white">
                Про систему
              </div>
            </div>

            <q-list dense class="text-white">
              <q-item class="q-px-none">
                <q-item-section avatar>
                  <q-icon name="mdi-robot" color="cyan-4" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-medium">RAG</q-item-label>
                  <q-item-label caption class="text-grey-4">Активний</q-item-label>
                </q-item-section>
              </q-item>

              <q-item class="q-px-none">
                <q-item-section avatar>
                  <q-icon name="mdi-heart" color="purple-4" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-medium">{{ stats.llm_model || 'GPT-5 Nano' }}</q-item-label>
                  <q-item-label caption class="text-grey-4">Мовна модель</q-item-label>
                </q-item-section>
              </q-item>

              <q-item class="q-px-none">
                <q-item-section avatar>
                  <q-icon
                    :name="systemStatus === 'healthy' ? 'mdi-check-circle' : 'mdi-loading mdi-spin'"
                    :color="systemStatus === 'healthy' ? 'positive' : 'warning'"
                  />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-medium">
                    {{ systemStatus === 'healthy' ? 'Готовий' : 'Завантаження' }}
                  </q-item-label>
                  <q-item-label caption class="text-grey-4">Статус системи</q-item-label>
                </q-item-section>
              </q-item>

            </q-list>
          </div>
        </div>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>

    <q-footer elevated class="bg-grey-9 text-white q-pa-sm">
      <div class="row items-center justify-between">
        <div class="text-caption">
          © {{ currentYear }} Інтелектуальний навігатор з нормативних документів КНУТШ
        </div>
        <div class="text-caption">
          Створено Степанюком Олексієм
        </div>
      </div>
    </q-footer>
  </q-layout>
</template>

<script>
import { defineComponent, ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from '@/api/axios'

export default defineComponent({
  name: 'MainLayout',

  setup() {
    const $q = useQuasar()
    const leftDrawerOpen = ref(false)
    const stats = ref({})
    const systemStatus = ref('initializing')

    const currentYear = new Date().getFullYear()

    const toggleLeftDrawer = () => {
      leftDrawerOpen.value = !leftDrawerOpen.value
    }

    const loadStats = async () => {
      try {
        const healthResponse = await api.get('/health')
        systemStatus.value = healthResponse.data.status

        const statsResponse = await api.get('/stats')
        stats.value = statsResponse.data.configuration
        stats.value.vector_store_size = statsResponse.data.statistics.vector_store_size
      } catch (error) {
        console.error('Не вдалося завантажити статистику:', error)
      }
    }

    onMounted(() => {
      loadStats()
      setInterval(loadStats, 30000)
    })

    return {
      leftDrawerOpen,
      toggleLeftDrawer,
      stats,
      systemStatus,
      currentYear
    }
  }
})
</script>

<style lang="scss" scoped>
.bg-gradient-primary {
  background: linear-gradient(135deg, #1976D2 0%, #2196F3 50%, #64B5F6 100%);
}

.bg-drawer {
  background: linear-gradient(180deg,
    rgba(var(--q-dark), 0.95) 0%,
    rgba(var(--q-dark), 0.98) 100%
  );
}

.q-item {
  transition: all 0.3s ease;

  &:hover {
    transform: translateX(5px);
  }
}

.system-info-card {
  background: linear-gradient(135deg, #1976D2 0%, #2196F3 50%, #42A5F5 100%);
  border: 2px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(25, 118, 210, 0.3);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    animation: pulse-glow 3s ease-in-out infinite;
  }
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}
</style>
