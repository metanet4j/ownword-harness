import type {ReactElement, ReactNode} from 'react';

export interface FormProps {
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

export declare function Form(props: FormProps): ReactElement;
