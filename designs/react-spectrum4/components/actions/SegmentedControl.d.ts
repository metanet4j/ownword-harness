import type {ReactElement} from 'react';

export interface SegmentedControlProps {
  label?: string;
  isDisabled?: boolean;
  defaultSelectedKey?: string;
  items?: Array<{key: string; label: string}>;
  onChange?: (key: string) => void;
}

export declare function SegmentedControl(props: SegmentedControlProps): ReactElement;
