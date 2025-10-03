import React from "react";
import * as Select from "@radix-ui/react-select";
import {
  CheckIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from "@radix-ui/react-icons"; // Or your preferred icons
import type { ModelAvailabilityMap, ModelAvailabilityInfo } from "../../types";

interface ModelSelectComponentProps {
  models: ModelAvailabilityMap;
  selectedModelName?: string;
  onSelectedModelChange: (modelName: string | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const ModelSelectComponent: React.FC<ModelSelectComponentProps> = ({
  models,
  selectedModelName,
  onSelectedModelChange,
  placeholder = "Select a model...",
  disabled = false,
}) => {
  const modelEntries = Object.entries<ModelAvailabilityInfo>(models);

  return (
    <Select.Root
      value={selectedModelName}
      onValueChange={(value) => {
        onSelectedModelChange(value === "" ? undefined : value);
      }}
      disabled={disabled}
    >
      <Select.Trigger
        className="inline-flex items-center justify-center rounded px-[15px] text-[13px] leading-none h-[35px] gap-[5px] bg-white text-violet11 shadow-[0_2px_10px] shadow-black/10 hover:bg-mauve3 focus:shadow-[0_0_0_2px] focus:shadow-black data-[placeholder]:text-violet9 outline-none dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600 dark:focus:shadow-violet-700 data-[placeholder]:dark:text-gray-400"
        aria-label="Select AI Model"
      >
        <Select.Value placeholder={placeholder} />
        <Select.Icon className="text-violet11 dark:text-gray-300">
          <ChevronDownIcon />
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="overflow-hidden bg-white rounded-md shadow-[0px_10px_38px_-10px_rgba(22,_23,_24,_0.35),0px_10px_20px_-15px_rgba(22,_23,_24,_0.2)] dark:bg-gray-800 dark:shadow-gray-900/50">
          <Select.ScrollUpButton className="flex items-center justify-center h-[25px] bg-white text-violet11 cursor-default dark:bg-gray-800 dark:text-gray-200">
            <ChevronUpIcon />
          </Select.ScrollUpButton>
          <Select.Viewport className="p-[5px]">
            <Select.Group>
              {modelEntries.length === 0 && (
                <div className="text-xs text-gray-500 px-[25px] py-[5px] dark:text-gray-400">
                  No models available.
                </div>
              )}
              {modelEntries.map(([name, modelInfo]) => (
                <Select.Item
                  key={name}
                  value={name}
                  className="text-[13px] leading-none text-violet11 rounded-[3px] flex items-center h-[25px] pr-[35px] pl-[25px] relative select-none data-[disabled]:text-mauve8 data-[disabled]:pointer-events-none data-[highlighted]:outline-none data-[highlighted]:bg-violet9 data-[highlighted]:text-violet1 dark:text-gray-200 dark:data-[highlighted]:bg-violet-500 dark:data-[highlighted]:text-gray-50"
                >
                  <Select.ItemText>
                    {modelInfo.display_name || name}
                  </Select.ItemText>
                  <Select.ItemIndicator className="absolute left-0 w-[25px] inline-flex items-center justify-center">
                    <CheckIcon />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Group>
          </Select.Viewport>
          <Select.ScrollDownButton className="flex items-center justify-center h-[25px] bg-white text-violet11 cursor-default dark:bg-gray-800 dark:text-gray-200">
            <ChevronDownIcon />
          </Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
};
