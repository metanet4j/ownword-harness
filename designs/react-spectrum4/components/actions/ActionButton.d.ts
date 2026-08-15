import type {ReactElement, ReactNode} from 'react';

export interface ActionButtonProps {
  children?: ReactNode;
  size?: 'S' | 'M' | 'L' | 'XL';
  isQuiet?: boolean;
  isDisabled?: boolean;
  isSelected?: boolean;
  isEmphasized?: boolean;
  staticColor?: 'white' | 'black' | 'auto';
  onPress?: () => void;
  'aria-label'?: string;
}

export declare function ActionButton(props: ActionButtonProps): ReactElement;
