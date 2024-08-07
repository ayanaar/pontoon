import { useContext } from 'react';

import { EditorActions } from '~/context/Editor';
import { EntityView } from '~/context/EntityView';
import { FailedChecksData } from '~/context/FailedChecksData';
import { HelperSelection } from '~/context/HelperSelection';
import { MachineryTranslations } from '~/context/MachineryTranslations';
import { SearchData } from '~/context/SearchData';
import { UnsavedActions, UnsavedChanges } from '~/context/UnsavedChanges';
import { useAppSelector } from '~/hooks';
import { getPlainMessage } from '~/utils/message';
import { useLLMTranslation } from '~/context/TranslationContext';
import type { SourceType } from '~/api/machinery';

import { useExistingTranslationGetter } from '../../editor/hooks/useExistingTranslationGetter';
import { useSendTranslation } from '../../editor/hooks/useSendTranslation';
import { useUpdateTranslationStatus } from '../../editor/hooks/useUpdateTranslationStatus';

/**
 *  On Enter:
 *   - If unsaved changes popup is shown, proceed.
 *   - If failed checks popup is shown after approving a translation, approve it anyway.
 *   - In other cases, send current translation.
 */
export function useHandleEnter(): () => true {
  const sendTranslation = useSendTranslation();
  const updateTranslationStatus = useUpdateTranslationStatus();
  const { resetUnsavedChanges } = useContext(UnsavedActions);
  const unsavedChanges = useContext(UnsavedChanges);
  const getExistingTranslation = useExistingTranslationGetter();
  const { errors, source, warnings } = useContext(FailedChecksData);

  return () => {
    const ignoreWarnings = errors.length + warnings.length > 0;

    if (unsavedChanges.onIgnore) {
      // There are unsaved changes, proceed.
      resetUnsavedChanges(true);
    } else if (typeof source === 'number') {
      // Approve anyway.
      updateTranslationStatus(source, 'approve', ignoreWarnings);
    } else {
      const existingTranslation = getExistingTranslation();
      if (existingTranslation && !existingTranslation.approved) {
        updateTranslationStatus(
          existingTranslation.pk,
          'approve',
          ignoreWarnings,
        );
      } else {
        sendTranslation(ignoreWarnings);
      }
    }
    return true;
  };
}

/** On Esc, close unsaved changes and failed checks popups if open. */
export function useHandleEscape(): () => boolean {
  const { resetUnsavedChanges } = useContext(UnsavedActions);
  const unsavedChanges = useContext(UnsavedChanges);
  const { errors, warnings, resetFailedChecks } = useContext(FailedChecksData);

  return () => {
    if (unsavedChanges.onIgnore) {
      // Close unsaved changes popup
      resetUnsavedChanges(false);
      return true;
    } else if (errors.length || warnings.length) {
      // Close failed checks popup
      resetFailedChecks();
      return true;
    }
    return false;
  };
}

/**
 * On Ctrl + Shift + Up/Down, copy next/previous entry from active
 * helper tab (Machinery or Locales) into translation.
 */
export function useHandleCtrlShiftArrow(): (
  key: 'ArrowDown' | 'ArrowUp',
) => boolean {
  const { entity } = useContext(EntityView);
  const { setEditorFromHelpers } = useContext(EditorActions);
  const helperSelection = useContext(HelperSelection);
  const { translations: machineryTranslations } = useContext(
    MachineryTranslations,
  );
  const { results: concordanceSearchResults } = useContext(SearchData);
  const otherLocaleTranslations = useAppSelector(
    (state) => state.otherlocales.translations,
  );

  const { tab, element, setElement } = helperSelection;
  const isMachinery = tab === 0;
  const numTranslations = isMachinery
    ? machineryTranslations.length + concordanceSearchResults.length
    : otherLocaleTranslations.length;

  // Precompute LLM state at the top level
  let llmState = null;
  if (isMachinery && element < machineryTranslations.length) {
    llmState = useLLMTranslation(machineryTranslations[element]);
  }

  return (key) => {
    if (numTranslations === 0) {
      return false;
    }
    const nextIdx =
      key === 'ArrowDown'
        ? (element + 1) % numTranslations
        : (element - 1 + numTranslations) % numTranslations;
    setElement(nextIdx);

    if (isMachinery) {
      const len = machineryTranslations.length;
      const translationObj =
        nextIdx < len
          ? machineryTranslations[nextIdx]
          : concordanceSearchResults[nextIdx - len];

      // If we have a valid LLM state, process it
      if (llmState) {
        const { translation, sources } = translationObj;
        const { llmTranslations, selectedOption } = llmState;

        // Check if there's an LLM translation available
        const llmTranslation = llmTranslations[selectedOption];
        const updatedSources: SourceType[] = llmTranslation
          ? ['gpt-transform']
          : sources;

        setEditorFromHelpers(llmTranslation || translation, updatedSources, true);
      }
    } else {
      const { translation } = otherLocaleTranslations[nextIdx];

      setEditorFromHelpers(
        getPlainMessage(translation, entity.format),
        [],
        true,
      );
    }
    return true;
  };
}
