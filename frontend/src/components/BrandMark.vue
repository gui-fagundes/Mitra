<script setup lang="ts">
/**
 * Logo do Mitra: losango preto com miolo dourado + wordmark em Josefin Sans.
 *   size = 'sm' (16px) para topos de mobile e cards.
 *   size = 'lg' (18px) para navegação desktop.
 * O componente é apenas visual; envolver em <router-link to="/"> nos usos.
 */
withDefaults(defineProps<{ size?: 'sm' | 'lg' }>(), {
  size: 'sm',
})
</script>

<template>
  <div class="flex items-center gap-2">
    <span
      class="relative shrink-0 rotate-45 rounded-[2px] bg-ink"
      :class="size === 'lg' ? 'h-[18px] w-[18px]' : 'h-4 w-4'"
    >
      <span class="absolute inset-[2px] rounded-[1px] bg-gold"></span>
    </span>
    <span
      class="font-sans font-semibold text-ink"
      :class="size === 'lg' ? 'text-[20px] tracking-[-0.015em]' : 'text-[18px] tracking-[-0.01em]'"
    >
      Mitra
    </span>
  </div>
</template>
