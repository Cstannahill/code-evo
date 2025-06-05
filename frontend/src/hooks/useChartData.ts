import { useMemo } from "react";
import { memoize } from "lodash";

export const useChartData = <TData, TTransformedData>(
  data: TData,
  transformer: (data: TData) => TTransformedData
): TTransformedData => {
  const memoizedTransformer = useMemo(
    () => memoize(transformer),
    [transformer]
  );

  return useMemo(() => memoizedTransformer(data), [data, memoizedTransformer]);
};
