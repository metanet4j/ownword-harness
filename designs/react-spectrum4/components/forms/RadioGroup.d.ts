import type {ReactElement, ReactNode} from 'react';

export interface RadioGroupProps {
  label?: string;
  children?: ReactNode;
  value?: string;
  defaultValue?: string;
  isDisabled?: boolean;
  isInvalid?: boolean;
  isReadOnly?: boolean;
  onChange?: (value: string) => void;
}

export declare function RadioGroup(props: RadioGroupProps): ReactElement;
