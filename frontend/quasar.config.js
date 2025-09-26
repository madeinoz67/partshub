const { configure } = require('quasar/wrappers')

module.exports = configure(function (ctx) {
  return {
    boot: [
      'axios',
      'pinia'
    ],

    css: [
    ],

    extras: [
      'roboto-font',
      'material-icons'
    ],

    build: {
      target: {
        browser: ['es2019', 'edge88', 'firefox78', 'chrome87', 'safari13.1'],
        node: 'node16'
      },
      vueRouterMode: 'history',
      extendViteConf(viteConf, { isServer, isClient }) {
        viteConf.resolve.alias = {
          ...viteConf.resolve.alias,
          '@': '/src'
        }
      }
    },

    devServer: {
      open: true,
      port: 3000,
      host: 'localhost'
    },

    framework: {
      config: {},
      plugins: [
        'Notify',
        'Dialog',
        'Loading',
        'LoadingBar'
      ]
    },

    supportTS: {
      tsCheckerConfig: {
        eslint: {
          enabled: true,
          files: './src/**/*.{ts,tsx,js,jsx,vue}'
        }
      }
    }
  }
})