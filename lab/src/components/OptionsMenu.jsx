import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import Slider from "@mui/material/Slider";
import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import FormLabel from "@mui/material/FormLabel";

export default function OptionsMenu() {
  let resolution = 256;

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        width: "100%",
      }}
    >
      <Box>
        <FormControl>
          <Box sx={{ width: 300, marginRight: 10 }}>
            <FormLabel>Image Resolution</FormLabel>
            <Slider
              aria-label="Image Resolution"
              defaultValue={resolution}
              valueLabelDisplay="auto"
              shiftStep={64}
              step={64}
              marks={[
                {
                  value: 128,
                  label: "128 px",
                },
                {
                  value: 1024,
                  label: "1024 px",
                },
              ]}
              min={128}
              max={1024}
              onChange={(_, value) => {
                resolution = value;
              }}
            />
          </Box>
        </FormControl>
        <ButtonGroup variant="outlined" aria-label="Basic button group">
          <Button
            onClick={() => {
              window.txtOutput.clear();
              window.txtOutput.appendLine("Beginning compile...");
              window.codeString = window.codeString.replace(/\r\n/g, "\n");
              compile_program(window.codeString);
            }}
          >
            Compile
          </Button>
          <Button
            onClick={() => {
              window.txtOutput.clear();
              window.txtOutput.appendLine("Beginning compile and run...");
              window.codeString = window.codeString.replace(/\r\n/g, "\n");
              compile_and_run_program(window.codeString, resolution);
            }}
          >
            Compile & Run
          </Button>
        </ButtonGroup>
      </Box>
    </Box>
  );
}
