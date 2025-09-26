import { boot } from 'quasar/wrappers'
import { createPinia } from 'pinia'

export default boot(({ app }) => {
  // Pinia is already configured in main.ts, but we need this file
  // for Quasar's boot system to work properly
  const pinia = createPinia()
  app.use(pinia)
})