{
  Mossy Manager - Detect Deleted Navmesh Records

  Purpose:
    Scan a plugin for deleted NAVM records without modifying anything.
    Outputs a report that can be parsed by Mossy Manager.

  Usage:
    Run this script in FO4Edit to scan for deleted navmesh.
    Results are written to the FO4Edit log.
}

unit MossyDetectDeletedNavmesh;

var
  deletedCount: integer;
  deletedRecords: TStringList;

function Initialize: integer;
begin
  Result := 0;
  deletedCount := 0;
  deletedRecords := TStringList.Create;

  AddMessage('MOSSY_SCAN_START: Deleted Navmesh Detection');
end;

function Process(e: IInterface): integer;
var
  sig: string;
  formID: string;
begin
  Result := 0;

  sig := Signature(e);

  if (sig = 'NAVM') and GetIsDeleted(e) then begin
    formID := IntToHex(GetLoadOrderFormID(e), 8);
    deletedRecords.Add(formID);
    deletedCount := deletedCount + 1;
    AddMessage('MOSSY_DELETED_NAVM: ' + formID + ' | ' + Name(e));
  end;
end;

function Finalize: integer;
var
  i: integer;
begin
  Result := 0;

  AddMessage('MOSSY_SCAN_RESULT: ' + IntToStr(deletedCount) + ' deleted NAVM records');

  deletedRecords.Free;
end;

end.
