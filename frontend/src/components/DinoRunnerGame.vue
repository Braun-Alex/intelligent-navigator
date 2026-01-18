<template>
  <div v-if="visible" class="dino-game-overlay" :class="{ 'fullscreen': isFullscreen }">
    <q-card flat bordered class="game-card">
      <!-- Заголовок з кнопками управління -->
      <q-card-section class="game-header bg-gradient-dino text-white">
        <div class="row items-center justify-between">
          <div class="col">
            <div class="text-h6">🦖 Dino Runner 🦖</div>
            <div class="text-caption">Біжіть і оглядайтеся лише вперед!</div>
          </div>
          <div class="col-auto">
            <q-chip color="white" text-color="primary" icon="mdi-star">
              {{ score }}
            </q-chip>
            <q-chip color="white" text-color="secondary" icon="mdi-trophy" class="q-ml-sm">
              🏆 {{ highScore }}
            </q-chip>
            <q-chip color="white" text-color="accent" icon="mdi-speedometer" class="q-ml-sm">
              ⚡ {{ Math.round(gameSpeed) }}
            </q-chip>
          </div>
          <div class="col-auto q-ml-md">
            <q-btn
              flat
              round
              dense
              :icon="isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
              color="white"
              @click="toggleFullscreen"
            >
              <q-tooltip>{{ isFullscreen ? 'Вийти з повноекранного режиму' : 'Повноекранний режим' }}</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              icon="mdi-close"
              color="white"
              @click="closeGame"
              class="q-ml-xs"
            >
              <q-tooltip>Закрити гру</q-tooltip>
            </q-btn>
          </div>
        </div>
      </q-card-section>

      <q-card-section class="game-canvas-section">
        <div v-if="!gameStarted && !gameOver" class="game-instructions">
          <div class="happy-dino-large">
            <div class="dino-body-large"></div>
            <div class="dino-head-large"></div>
            <div class="dino-eye-large"></div>
            <div class="dino-smile"></div>
          </div>
          <div class="text-h6 q-mt-md">Керування грою</div>
          <div class="q-mt-sm">
            <q-chip color="primary" text-color="white" icon="mdi-arrow-up-bold">↑</q-chip>
            <span class="q-mx-sm">- рух вгору</span>
          </div>
          <div class="q-mt-xs">
            <q-chip color="primary" text-color="white" icon="mdi-arrow-down-bold">↓</q-chip>
            <span class="q-mx-sm">- рух вниз</span>
          </div>
          <div class="text-caption text-grey-7 q-mt-md">
            Уникайте кактусів та ворожих динозаврів!<br>
            Стежте за погодою! ⚡
          </div>
          <q-btn
            unelevated
            color="primary"
            label="Почати гру"
            icon="mdi-play"
            size="lg"
            @click="startGame"
            class="q-mt-md"
          />
        </div>

        <canvas
          ref="gameCanvas"
          :width="canvasWidth"
          :height="canvasHeight"
          class="game-canvas"
          :class="{ 'canvas-active': gameStarted && !gameOver }"
        ></canvas>

        <div v-if="gameOver" class="game-over-overlay">
          <div class="game-over-content">
            <div class="happy-dino-game-over">
              <div class="dino-body-go"></div>
              <div class="dino-head-go"></div>
              <div class="dino-eye-go eye-left"></div>
              <div class="dino-eye-go eye-right"></div>
              <div class="dino-sad-mouth"></div>
              <div class="dino-arm arm-left"></div>
              <div class="dino-arm arm-right"></div>
            </div>
            
            <div class="text-h5 text-weight-bold q-mt-md">{{ getGameOverMessage() }}</div>
            <div class="text-h3 text-weight-bold text-primary q-mt-sm">{{ score }}</div>
            <div class="text-caption text-grey-7">Відстань: {{ Math.round(distance) }}м</div>
            <div v-if="score > highScore" class="text-positive q-mt-sm">
              🎉 Новий рекорд!
            </div>
            <div v-else-if="score > highScore * 0.9" class="text-info q-mt-sm">
              💪 Майже рекорд! Ще {{ highScore - score }} очок!
            </div>
            <q-btn
              unelevated
              color="primary"
              label="Грати ще раз"
              icon="mdi-restart"
              @click="restartGame"
              class="q-mt-md"
            />
          </div>
        </div>
      </q-card-section>

      <q-card-section class="game-stats bg-grey-2">
        <div class="row items-center justify-around text-center">
          <div class="col">
            <div class="text-h6 text-weight-bold">{{ obstaclesAvoided }}</div>
            <div class="text-caption text-grey-7">Перешкод</div>
          </div>
          <q-separator vertical />
          <div class="col">
            <div class="text-h6 text-weight-bold">{{ enemiesAvoided }}</div>
            <div class="text-caption text-grey-7">Ворогів</div>
          </div>
          <q-separator vertical />
          <div class="col">
            <div class="text-h6 text-weight-bold">{{ Math.round(distance) }} м</div>
            <div class="text-caption text-grey-7">Дистанція</div>
          </div>
          <q-separator vertical />
          <div class="col">
            <div class="text-subtitle2 text-weight-bold" :class="weatherClass">{{ weatherEmoji }}</div>
            <div class="text-caption text-grey-7">Погода</div>
          </div>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'

export default defineComponent({
  name: 'DinoRunnerGame',

  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },

  emits: ['close'],

  setup(props, { emit }) {
    const gameCanvas = ref(null)
    const canvasWidth = 800
    const canvasHeight = 300
    const gameStarted = ref(false)
    const gameOver = ref(false)
    const score = ref(0)
    const highScore = ref(0)
    const obstaclesAvoided = ref(0)
    const enemiesAvoided = ref(0)
    const distance = ref(0)
    const gameSpeed = ref(4)
    const isFullscreen = ref(false)
    const deathReason = ref('obstacle')

    let ctx = null
    let animationId = null
    let lastTime = 0
    let keysPressed = {}

    // Гравець (вертикальне переміщення)
    const player = {
      x: 80,
      y: 150, // Стартова позиція по центру
      width: 40,
      height: 40,
      velocityY: 0,
      maxSpeed: 5,
      acceleration: 0.5,
      deceleration: 0.3,
      color: '#4CAF50'
    }

    // Перешкоди та вороги
    const obstacles = []
    const enemies = []
    const particles = [] // Для дощу
    const lightning = { active: false, x: 0, alpha: 0 }
    
    let obstacleTimer = 0
    let enemyTimer = 0
    let weatherTimer = 0
    let difficultyTimer = 0
    let currentWeather = 'clear' // clear, rain, storm
    
    const loadHighScore = () => {
      const saved = localStorage.getItem('dinoGameHighScore')
      if (saved) {
        highScore.value = parseInt(saved)
      }
    }

    const saveHighScore = () => {
      if (score.value > highScore.value) {
        highScore.value = score.value
        localStorage.setItem('dinoGameHighScore', highScore.value.toString())
      }
    }

    const toggleFullscreen = () => {
      isFullscreen.value = !isFullscreen.value
    }

    const closeGame = () => {
      emit('close')
    }

    const weatherEmoji = computed(() => {
      if (currentWeather === 'storm') return '⚡'
      if (currentWeather === 'rain') return '🌧️'
      return '☀️'
    })

    const weatherClass = computed(() => {
      if (currentWeather === 'storm') return 'text-warning'
      if (currentWeather === 'rain') return 'text-info'
      return 'text-positive'
    })

    const getGameOverMessage = () => {
      const messages = {
        obstacle: ['Напоролися на кактус!', 'Повезе наступного разу!', 'Спробуйте ще!'],
        enemy: ['Вас схопив ворожий динозавр!', 'Будьте уважніші до ворогів!', 'Майже вдалося оминути!'],
        lightning: ['Вас уразила блискавка ⚡!', 'Погода була проти вас!', 'Не пощастило з погодою!']
      }
      const options = messages[deathReason.value] || messages.obstacle
      return options[Math.floor(Math.random() * options.length)]
    }

    const startGame = () => {
      gameStarted.value = true
      gameOver.value = false
      score.value = 0
      obstaclesAvoided.value = 0
      enemiesAvoided.value = 0
      distance.value = 0
      gameSpeed.value = 4
      obstacles.length = 0
      enemies.length = 0
      particles.length = 0
      obstacleTimer = 0
      enemyTimer = 0
      weatherTimer = 0
      difficultyTimer = 0
      currentWeather = 'clear'
      deathReason.value = 'obstacle'
      
      player.y = 150
      player.velocityY = 0
      keysPressed = {}

      gameLoop()
    }

    const restartGame = () => {
      startGame()
    }

    const handleKeyDown = (e) => {
      if (!props.visible || !gameStarted.value || gameOver.value) return
      
      if (e.code === 'ArrowUp' || e.code === 'ArrowDown') {
        e.preventDefault()
        keysPressed[e.code] = true
      }
    }

    const handleKeyUp = (e) => {
      if (!props.visible) return
      
      if (e.code === 'ArrowUp' || e.code === 'ArrowDown') {
        e.preventDefault()
        keysPressed[e.code] = false
      }
    }

    const createObstacle = () => {
      // Різні типи перешкод з різними позиціями по Y
      const types = [
        { width: 20, height: 40, color: '#F44336', y: canvasHeight - 80 }, // Низький
        { width: 25, height: 60, color: '#FF9800', y: canvasHeight - 100 }, // Середній
        { width: 30, height: 35, color: '#E91E63', y: 100 }, // Високий
        { width: 20, height: 45, color: '#9C27B0', y: 150 }, // Центр
      ]
      
      // В залежності від погоди - більше або менше перешкод
      const weatherMultiplier = currentWeather === 'rain' ? 1.5 : 1
      
      if (Math.random() < 0.3 * weatherMultiplier) {
        const type = types[Math.floor(Math.random() * types.length)]
        obstacles.push({
          x: canvasWidth,
          y: type.y,
          width: type.width,
          height: type.height,
          color: type.color,
          scored: false
        })
      }
    }

    const createEnemy = () => {
      // Ворожі динозаври - рухаються вниз або вгору
      if (Math.random() < 0.15) { // Шанс 15%
        const startY = 80 + Math.random() * 140
        enemies.push({
          x: canvasWidth,
          y: startY,
          width: 35,
          height: 35,
          color: '#D32F2F',
          velocityY: (Math.random() - 0.5) * 3, // Випадковий рух
          scored: false
        })
      }
    }

    const createRainParticles = () => {
      if (currentWeather === 'rain' || currentWeather === 'storm') {
        for (let i = 0; i < 3; i++) {
          particles.push({
            x: canvasWidth + Math.random() * 100,
            y: Math.random() * canvasHeight,
            speed: 5 + Math.random() * 3,
            length: 10 + Math.random() * 10
          })
        }
      }
    }

    const triggerLightning = () => {
      if (currentWeather === 'storm' && Math.random() < 0.02) { // Шанс 2% на кожен кадр
        lightning.active = true
        lightning.x = player.x - 50 + Math.random() * 100
        lightning.alpha = 1
        
        // Перевірка, чи вдарила блискавка у гравця
        if (Math.abs(lightning.x - player.x) < 30) {
          gameOver.value = true
          gameStarted.value = false
          deathReason.value = 'lightning'
          saveHighScore()
        }
      }
    }

    const updateWeather = () => {
      weatherTimer++
      
      // Зміна погоди кожні 500-1000 кадрів
      if (weatherTimer > 500 + Math.random() * 500) {
        const weathers = ['clear', 'rain', 'storm']
        // Більше шансів на погану погоду при вищій складності
        const stormChance = Math.min(distance.value / 500, 0.3)
        const rand = Math.random()
        
        if (rand < stormChance) {
          currentWeather = 'storm'
        } else if (rand < stormChance + 0.3) {
          currentWeather = 'rain'
        } else {
          currentWeather = 'clear'
        }
        
        weatherTimer = 0
      }
    }

    const updateDifficulty = () => {
      difficultyTimer++
      
      // Постійне зростання складності
      if (difficultyTimer > 60) { // Кожну секунду
        gameSpeed.value = Math.min(gameSpeed.value + 0.15, 25) // Максимум 25
        difficultyTimer = 0
      }
      
      // Випадкові події складності
      if (Math.random() < 0.001) { // Дуже рідко
        // Раптове збільшення швидкості
        gameSpeed.value = Math.min(gameSpeed.value + 2, 25)
      }
    }

    const checkCollision = (obj1, obj2) => {
      return obj1.x < obj2.x + obj2.width &&
             obj1.x + obj1.width > obj2.x &&
             obj1.y < obj2.y + obj2.height &&
             obj1.y + obj1.height > obj2.y
    }

    const drawPlayer = () => {
      // Тіло
      ctx.fillStyle = player.color
      ctx.fillRect(player.x, player.y, player.width, player.height)
      
      // Голова
      ctx.fillStyle = '#66BB6A'
      ctx.fillRect(player.x + 25, player.y - 10, 15, 15)
      
      // Око
      ctx.fillStyle = '#000'
      ctx.fillRect(player.x + 32, player.y - 7, 3, 3)
      
      // Лапки (анімація)
      const legOffset = Math.floor(Date.now() / 100) % 2 === 0 ? 3 : 0
      ctx.fillStyle = player.color
      ctx.fillRect(player.x + 5, player.y + 35 + legOffset, 8, 10)
      ctx.fillRect(player.x + 27, player.y + 35 - legOffset, 8, 10)
      
      // Хвіст
      ctx.fillStyle = '#81C784'
      ctx.fillRect(player.x - 5, player.y + 10, 10, 8)
    }

    const drawObstacle = (obstacle) => {
      ctx.fillStyle = obstacle.color
      ctx.fillRect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
      
      // Колючки
      ctx.fillStyle = '#C62828'
      for (let i = 0; i < obstacle.height; i += 8) {
        ctx.fillRect(obstacle.x - 2, obstacle.y + i, 4, 4)
        ctx.fillRect(obstacle.x + obstacle.width - 2, obstacle.y + i, 4, 4)
      }
    }

    const drawEnemy = (enemy) => {
      // Ворожий динозавр (червоний)
      ctx.fillStyle = enemy.color
      ctx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height)
      
      // Голова
      ctx.fillStyle = '#E57373'
      ctx.fillRect(enemy.x - 10, enemy.y - 8, 12, 12)
      
      // Око
      ctx.fillStyle = '#000'
      ctx.fillRect(enemy.x - 6, enemy.y - 5, 3, 3)
      
      // Зуби
      ctx.fillStyle = '#FFF'
      ctx.fillRect(enemy.x - 3, enemy.y + 2, 3, 4)
    }

    const drawWeather = () => {
      // Дощ
      if (currentWeather === 'rain' || currentWeather === 'storm') {
        ctx.strokeStyle = 'rgba(100, 150, 200, 0.5)'
        ctx.lineWidth = 1
        particles.forEach(p => {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p.x - 5, p.y + p.length)
          ctx.stroke()
        })
      }
      
      // Блискавка
      if (lightning.active && lightning.alpha > 0) {
        ctx.strokeStyle = `rgba(255, 255, 100, ${lightning.alpha})`
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.moveTo(lightning.x, 0)
        ctx.lineTo(lightning.x - 10, 100)
        ctx.lineTo(lightning.x + 5, 100)
        ctx.lineTo(lightning.x - 5, canvasHeight)
        ctx.stroke()
        
        lightning.alpha -= 0.05
        if (lightning.alpha <= 0) {
          lightning.active = false
        }
      }
    }

    const drawBackground = () => {
      // Небо (змінюється з погодою)
      let skyColor1, skyColor2
      if (currentWeather === 'storm') {
        skyColor1 = '#5a6c7d'
        skyColor2 = '#8a9ba8'
      } else if (currentWeather === 'rain') {
        skyColor1 = '#87CEEB'
        skyColor2 = '#B0C4DE'
      } else {
        skyColor1 = '#87CEEB'
        skyColor2 = '#E0F7FA'
      }
      
      const gradient = ctx.createLinearGradient(0, 0, 0, canvasHeight)
      gradient.addColorStop(0, skyColor1)
      gradient.addColorStop(1, skyColor2)
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)
      
      // Хмари (якщо не гроза)
      if (currentWeather !== 'storm') {
        const cloudOffset = (Date.now() / 50) % canvasWidth
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
        ctx.beginPath()
        ctx.arc(100 - cloudOffset, 30, 20, 0, Math.PI * 2)
        ctx.arc(120 - cloudOffset, 30, 25, 0, Math.PI * 2)
        ctx.arc(140 - cloudOffset, 30, 20, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    const gameLoop = (timestamp = 0) => {
      if (!ctx || gameOver.value) return

      const deltaTime = timestamp - lastTime
      lastTime = timestamp

      ctx.clearRect(0, 0, canvasWidth, canvasHeight)
      
      drawBackground()
      drawWeather()

      // Оновлення гравця (вертикальний рух)
      if (keysPressed['ArrowUp']) {
        player.velocityY = Math.max(player.velocityY - player.acceleration, -player.maxSpeed)
      } else if (keysPressed['ArrowDown']) {
        player.velocityY = Math.min(player.velocityY + player.acceleration, player.maxSpeed)
      } else {
        // Плавне гальмування
        if (player.velocityY > 0) {
          player.velocityY = Math.max(0, player.velocityY - player.deceleration)
        } else if (player.velocityY < 0) {
          player.velocityY = Math.min(0, player.velocityY + player.deceleration)
        }
      }

      player.y += player.velocityY

      // Обмеження руху
      if (player.y < 50) {
        player.y = 50
        player.velocityY = 0
      }
      if (player.y > canvasHeight - player.height - 20) {
        player.y = canvasHeight - player.height - 20
        player.velocityY = 0
      }

      drawPlayer()

      // Створення перешкод
      obstacleTimer++
      if (obstacleTimer > Math.max(60 - gameSpeed.value * 2, 20)) {
        createObstacle()
        obstacleTimer = 0
      }

      // Створення ворогів
      enemyTimer++
      if (enemyTimer > 150) {
        createEnemy()
        enemyTimer = 0
      }

      // Оновлення погоди
      updateWeather()
      createRainParticles()
      triggerLightning()
      
      // Оновлення складності
      updateDifficulty()

      // Оновлення перешкод
      for (let i = obstacles.length - 1; i >= 0; i--) {
        const obstacle = obstacles[i]
        obstacle.x -= gameSpeed.value

        drawObstacle(obstacle)

        if (checkCollision(player, obstacle)) {
          gameOver.value = true
          gameStarted.value = false
          deathReason.value = 'obstacle'
          saveHighScore()
          return
        }

        if (!obstacle.scored && obstacle.x + obstacle.width < player.x) {
          obstacle.scored = true
          obstaclesAvoided.value++
          score.value += 5
        }

        if (obstacle.x + obstacle.width < 0) {
          obstacles.splice(i, 1)
        }
      }

      // Оновлення ворогів
      for (let i = enemies.length - 1; i >= 0; i--) {
        const enemy = enemies[i]
        enemy.x -= gameSpeed.value
        enemy.y += enemy.velocityY

        // Відбивання від меж
        if (enemy.y < 50 || enemy.y > canvasHeight - enemy.height - 20) {
          enemy.velocityY = -enemy.velocityY
        }

        drawEnemy(enemy)

        if (checkCollision(player, enemy)) {
          gameOver.value = true
          gameStarted.value = false
          deathReason.value = 'enemy'
          saveHighScore()
          return
        }

        if (!enemy.scored && enemy.x + enemy.width < player.x) {
          enemy.scored = true
          enemiesAvoided.value++
          score.value += 15
        }

        if (enemy.x + enemy.width < 0) {
          enemies.splice(i, 1)
        }
      }

      // Оновлення дощових частинок
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]
        p.x -= p.speed
        if (p.x < 0) {
          particles.splice(i, 1)
        }
      }

      distance.value += gameSpeed.value * 0.02
      score.value = Math.floor(distance.value)

      animationId = requestAnimationFrame(gameLoop)
    }

    const initCanvas = () => {
      if (gameCanvas.value) {
        ctx = gameCanvas.value.getContext('2d')
        loadHighScore()
      }
    }

    watch(() => props.visible, (newVal) => {
      if (newVal) {
        setTimeout(() => {
          initCanvas()
        }, 100)
      } else {
        if (animationId) {
          cancelAnimationFrame(animationId)
        }
        gameStarted.value = false
        gameOver.value = false
        isFullscreen.value = false
        keysPressed = {}
      }
    })

    onMounted(() => {
      document.addEventListener('keydown', handleKeyDown)
      document.addEventListener('keyup', handleKeyUp)
      if (props.visible) {
        initCanvas()
      }
    })

    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('keyup', handleKeyUp)
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    })

    return {
      gameCanvas,
      canvasWidth,
      canvasHeight,
      gameStarted,
      gameOver,
      score,
      highScore,
      obstaclesAvoided,
      enemiesAvoided,
      distance,
      gameSpeed,
      isFullscreen,
      weatherEmoji,
      weatherClass,
      startGame,
      restartGame,
      toggleFullscreen,
      closeGame,
      getGameOverMessage
    }
  }
})
</script>

<style lang="scss" scoped>
.dino-game-overlay {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 9999;
  width: 90%;
  max-width: 850px;
  animation: slideInScale 0.5s ease;
  transition: all 0.3s ease;

  &.fullscreen {
    width: 100vw;
    height: 100vh;
    max-width: none;
    border-radius: 0;

    .game-card {
      height: 100vh;
      border-radius: 0;
    }

    .game-canvas {
      width: 100%;
      height: calc(100vh - 220px);
    }
  }
}

@keyframes slideInScale {
  from {
    opacity: 0;
    transform: translate(-50%, -60%) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.game-card {
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.bg-gradient-dino {
  background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
}

.game-canvas-section {
  position: relative;
  padding: 0;
  background: #E3F2FD;
}

.game-instructions {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.game-canvas {
  display: block;
  cursor: crosshair;
  border-bottom: 1px solid #ddd;
}

.canvas-active {
  cursor: crosshair;
}

.game-over-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease;
}

.game-over-content {
  text-align: center;
  color: white;
  padding: 32px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.game-stats {
  padding: 12px 16px;
}

.happy-dino-large {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto;
  animation: bounce 2s infinite;
}

.dino-body-large {
  width: 50px;
  height: 50px;
  background: #4CAF50;
  border-radius: 8px;
  position: absolute;
  left: 15px;
  bottom: 10px;
}

.dino-head-large {
  width: 35px;
  height: 35px;
  background: #66BB6A;
  border-radius: 6px;
  position: absolute;
  right: 10px;
  top: 0;
}

.dino-eye-large {
  width: 8px;
  height: 8px;
  background: #000;
  border-radius: 50%;
  position: absolute;
  right: 15px;
  top: 8px;
}

.dino-smile {
  width: 15px;
  height: 8px;
  border: 3px solid #000;
  border-top: none;
  border-radius: 0 0 15px 15px;
  position: absolute;
  right: 12px;
  top: 20px;
}

.happy-dino-game-over {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto;
  animation: sad-bounce 1s ease-in-out infinite;
}

.dino-body-go {
  width: 60px;
  height: 60px;
  background: #4CAF50;
  border-radius: 10px;
  position: absolute;
  left: 20px;
  bottom: 10px;
}

.dino-head-go {
  width: 45px;
  height: 45px;
  background: #66BB6A;
  border-radius: 8px;
  position: absolute;
  right: 10px;
  top: 5px;
}

.dino-eye-go {
  width: 10px;
  height: 10px;
  background: #000;
  border-radius: 50%;
  position: absolute;
  top: 12px;

  &.eye-left {
    left: 8px;
  }

  &.eye-right {
    right: 8px;
  }
}

.dino-sad-mouth {
  width: 20px;
  height: 10px;
  border: 3px solid #000;
  border-bottom: none;
  border-radius: 15px 15px 0 0;
  position: absolute;
  right: 20px;
  top: 30px;
  transform: rotate(180deg);
}

.dino-arm {
  width: 8px;
  height: 25px;
  background: #4CAF50;
  border-radius: 4px;
  position: absolute;
  bottom: 30px;

  &.arm-left {
    left: 15px;
    transform: rotate(-20deg);
  }

  &.arm-right {
    right: 15px;
    transform: rotate(20deg);
  }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes sad-bounce {
  0%, 100% { transform: translateY(0) rotate(-5deg); }
  50% { transform: translateY(-5px) rotate(5deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
