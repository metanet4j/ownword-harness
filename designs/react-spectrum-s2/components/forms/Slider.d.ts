import type {ReactElement, ReactNode} from 'react';

export interface SliderProps {
  children?: ReactNode;
  label?: string;
  description?: string;
  value?: string | number;
  variant?: 'accent' | 'primary' | 'secondary' | 'negative' | 'premium' | 'genai' | 'neutral' | 'quiet';
  fillStyle?: 'fill' | 'outline';
  size?: 'XS' | 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isSelected?: boolean;
  isQuiet?: boolean;
  isEmphasized?: boolean;
  onPress?: () => void;
  className?: string;
  'aria-label'?: string;
}

export declare function Slider(props: SliderProps): ReactElement;
