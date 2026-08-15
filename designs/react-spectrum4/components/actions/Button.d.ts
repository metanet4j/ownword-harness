import type {ReactElement, ReactNode} from 'react';

export interface ButtonProps {
  children?: ReactNode;
  variant?: 'primary' | 'secondary' | 'accent' | 'negative' | 'premium' | 'genai';
  fillStyle?: 'fill' | 'outline';
  size?: 'S' | 'M' | 'L' | 'XL';
  staticColor?: 'white' | 'black' | 'auto';
  isDisabled?: boolean;
  isPending?: boolean;
  onPress?: () => void;
  className?: string;
  'aria-label'?: string;
}

export declare function Button(props: ButtonProps): ReactElement;
