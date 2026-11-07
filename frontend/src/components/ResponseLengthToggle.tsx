import type { ResponseType } from '../types'

type Props = {
  value: ResponseType
  onChange: (value: ResponseType) => void
  disabled?: boolean
}

export function ResponseLengthToggle({ value, onChange, disabled }: Props) {
  return (
    <div className="length-toggle" role="radiogroup" aria-label="Response length">
      <button
        type="button"
        role="radio"
        aria-checked={value === 'short'}
        className={value === 'short' ? 'is-active' : undefined}
        disabled={disabled}
        onClick={() => onChange('short')}
      >
        Short
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={value === 'long'}
        className={value === 'long' ? 'is-active' : undefined}
        disabled={disabled}
        onClick={() => onChange('long')}
      >
        Long
      </button>
    </div>
  )
}
