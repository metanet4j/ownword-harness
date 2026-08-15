import type {ReactElement, ReactNode} from 'react';

export interface SwitchProps {
  children?: ReactNode;
  isSelected?: boolean;
  defaultSelected?: boolean;
  isDisabled?: boolean;
  isEmphasized?: boolean;
  size?: 'S' | 'M' | 'L' | 'XL';
  onChange?: (isSelected: boolean) => void;
}

export declare function Switch(props: SwitchProps): ReactElement;
