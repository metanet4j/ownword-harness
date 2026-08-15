import type {ReactElement, ReactNode} from 'react';

export interface GridProps {
  children?: ReactNode;
  label?: string;
  description?: string;
  value?: string | number;
  variant?: 'accent' | 'primary' | 'secondary' | 'negative' | 'quiet';
  size?: 'S' | 'M' | 'L';
  isDisabled?: boolean;
  isSelected?: boolean;
  isQuiet?: boolean;
  onPress?: () => void;
  className?: string;
  'aria-label'?: string;
}

export declare function Grid(props: GridProps): ReactElement;
