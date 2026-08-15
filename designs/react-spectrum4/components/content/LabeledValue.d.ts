import type {ReactElement} from 'react';

export interface LabeledValueProps {
  label?: string;
  value?: string | number;
}

export declare function LabeledValue(props: LabeledValueProps): ReactElement;
