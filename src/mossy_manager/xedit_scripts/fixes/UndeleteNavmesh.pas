{
  Mossy Manager - Undelete and Disable Navmesh Records

  Purpose:
    Fix deleted NAVM (navmesh) records which cause instant CTD in Fallout 4.
    Uses the standard modding practice: undelete the record and set it as
    initially disabled.

  Usage:
    1. Load the plugin in FO4Edit
    2. Run this script
    3. Script will find and fix all deleted NAVM records

  Based on standard "Undelete and Disable References" practices from
  the xEdit community.
}

unit MossyUndeleteNavmesh;

var
  targetPlugin: IInterface;
  processedCount: integer;
  errorCount: integer;

{
  Initialize - Called once at start
}
function Initialize: integer;
begin
  Result := 0;
  processedCount := 0;
  errorCount := 0;

  AddMessage('=========================================================');
  AddMessage('Mossy Manager: Undelete and Disable Navmesh');
  AddMessage('=========================================================');
  AddMessage('');
  AddMessage('This script will fix deleted NAVM records that cause CTD.');
  AddMessage('Method: Undelete record + set Initially Disabled flag');
  AddMessage('');
end;

{
  Process - Called for each record selected
}
function Process(e: IInterface): integer;
var
  sig: string;
  recordFlags: integer;
  isDeleted: boolean;
  formID: string;
begin
  Result := 0;

  // Get record signature (NAVM, CELL, etc.)
  sig := Signature(e);

  // Only process NAVM records
  if sig <> 'NAVM' then
    Exit;

  // Check if record is deleted
  isDeleted := GetIsDeleted(e);

  if not isDeleted then begin
    // Not deleted, skip it
    Exit;
  end;

  // This is a deleted NAVM record - FIX IT!
  formID := IntToHex(GetLoadOrderFormID(e), 8);

  AddMessage('');
  AddMessage('Found deleted NAVM: ' + formID + ' - ' + Name(e));

  try
    // Step 1: Undelete the record
    SetIsDeleted(e, False);
    AddMessage('  [1/2] Undeleted record');

    // Step 2: Set Initially Disabled flag
    // This prevents the navmesh from being used in-game but keeps
    // the record intact so references to it don't cause CTD
    SetIsInitiallyDisabled(e, True);
    AddMessage('  [2/2] Set Initially Disabled flag');

    AddMessage('  STATUS: FIXED');
    processedCount := processedCount + 1;

  except
    on Ex: Exception do begin
      AddMessage('  ERROR: Failed to fix - ' + Ex.Message);
      errorCount := errorCount + 1;
    end;
  end;
end;

{
  Finalize - Called once at end
}
function Finalize: integer;
begin
  Result := 0;

  AddMessage('');
  AddMessage('=========================================================');
  AddMessage('Mossy Manager: Undelete Navmesh Complete');
  AddMessage('=========================================================');
  AddMessage('');
  AddMessage('Processed: ' + IntToStr(processedCount) + ' deleted NAVM records');

  if errorCount > 0 then begin
    AddMessage('Errors: ' + IntToStr(errorCount) + ' records could not be fixed');
    AddMessage('');
    AddMessage('WARNING: Some records failed to fix. Check messages above.');
  end else if processedCount = 0 then begin
    AddMessage('Result: No deleted navmesh records found.');
    AddMessage('');
    AddMessage('This is good! Your mod does not have the deleted NAVM issue.');
  end else begin
    AddMessage('Result: All deleted navmesh records have been fixed!');
    AddMessage('');
    AddMessage('IMPORTANT: Save your plugin to keep these fixes.');
  end;

  AddMessage('=========================================================');
end;

end.
