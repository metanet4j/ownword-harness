import type {ReactElement, ReactNode} from 'react';

export interface CheckboxProps {
  children?: ReactNode;
  isSelected?: boolean;
  defaultSelected?: boolean;
  isIndeterminate?: boolean;
  isDisabled?: boolean;
  isInvalid?: boolean;
  isEmphasized?: boolean;
  size?: 'S' | 'M' | 'L' | 'XL';
  onChange?: (isSelected: boolean) => void;
}

export declare function Checkbox(props: CheckboxProps): ReactElement;
