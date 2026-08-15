import type {ReactElement, ReactNode} from 'react';

export interface ToggleButtonProps {
  children?: ReactNode;
  variant?: 'accent' | 'primary' | 'secondary' | 'negative';
  fillStyle?: 'fill' | 'outline';
  size?: 'S' | 'M' | 'L' | 'XL';
  isDisabled?: boolean;
  isSelected?: boolean;
  isEmphasized?: boolean;
  onPress?: () => void;
  'aria-label'?: string;
}

export declare function ToggleButton(props: ToggleButtonProps): ReactElement;
