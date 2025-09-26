<template>
  <div id="q-app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// PartsHub main app component
</script>

<style lang="scss">
#q-app {
  height: 100vh;
}

// Global styles for the application
body {
  font-family: 'Roboto', sans-serif;
}

// Utility classes
.full-width {
  width: 100%;
}

.text-weight-medium {
  font-weight: 500;
}

// Status color overrides
.text-positive {
  color: #4caf50 !important;
}

.text-negative {
  color: #f44336 !important;
}

.text-warning {
  color: #ff9800 !important;
}

// Card enhancements
.q-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);

  &:hover {
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
  }
}
</style>