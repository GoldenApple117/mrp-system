import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SkeletonCard from '@/components/common/SkeletonCard.vue'

describe('SkeletonCard', () => {
  it('renders correct number of placeholder cards', () => {
    const wrapper = mount(SkeletonCard, { props: { count: 4 } })
    const cards = wrapper.findAll('.animate-pulse > div')
    expect(cards).toHaveLength(4)
  })

  it('defaults to 4 cards', () => {
    const wrapper = mount(SkeletonCard)
    const cards = wrapper.findAll('.animate-pulse > div')
    expect(cards).toHaveLength(4)
  })
})
