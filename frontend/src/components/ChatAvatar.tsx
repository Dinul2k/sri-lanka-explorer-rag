import Avatar, { genConfig } from 'react-nice-avatar'

const botConfig = genConfig({
  sex: 'man',
  hairStyle: 'thick',
  hairColor: '#1f2937',
  eyeStyle: 'circle',
  glassesStyle: 'round',
  noseStyle: 'round',
  mouthStyle: 'smile',
  shirtStyle: 'hoody',
  shirtColor: '#0f766e',
  bgColor: '#10a37f',
  faceColor: '#F9C9B6',
  earSize: 'small',
  hatStyle: 'none',
})

const userConfig = genConfig({
  sex: 'woman',
  hairStyle: 'womanShort',
  hairColor: '#4a3728',
  eyeStyle: 'oval',
  glassesStyle: 'none',
  noseStyle: 'short',
  mouthStyle: 'peace',
  shirtStyle: 'polo',
  shirtColor: '#64748b',
  bgColor: '#e2e8f0',
  faceColor: '#F9C9B6',
  earSize: 'small',
  hatStyle: 'none',
})

type Props = {
  role: 'user' | 'assistant'
  size?: number
  className?: string
}

export function ChatAvatar({ role, size = 34, className }: Props) {
  const config = role === 'assistant' ? botConfig : userConfig
  return (
    <span className={className} aria-hidden>
      <Avatar
        style={{ width: size, height: size }}
        shape="circle"
        {...config}
      />
    </span>
  )
}
