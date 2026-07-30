package com.logitrack.logitrack.controller;


import com.logitrack.logitrack.dto.EnvioDTO;
import com.logitrack.logitrack.model.Envio;
import com.logitrack.logitrack.service.EnvioService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController //Le dice a Spring que esta clase va a manejar las peticiones HTTP (GET- PUT - POST - DELETE)
@RequestMapping("/api/envios") //http://localhost:8080/api/envios
public class EnvioController {

    //Inyeccion de dependencias por constructor

    private final EnvioService envioService;

    @Autowired
    public EnvioController(EnvioService envioService){
        this.envioService = envioService;
    }

    @GetMapping
    public List<EnvioDTO> getAllEnvios(){
        List<Envio> envios = envioService.findAll();
        return envios.stream()
                .map(EnvioDTO::fromEntity)
                .collect(Collectors.toList());
    }

    @GetMapping("/{id}")
    public EnvioDTO getEnvioById(@PathVariable String id){
        Envio envio = envioService.findById(id);
        return EnvioDTO.fromEntity(envio);
    }

    @GetMapping("/estado/{estado}")
    public List<Envio> getEnviosByEstado(@PathVariable String estado){
        return envioService.findByEstado(estado);
    }

    @PostMapping // Crear nuevo
    public EnvioDTO createEnvio(@RequestBody EnvioDTO envioDTO){
        Envio envio = envioDTO.toEntity();
        Envio envioGuardado = envioService.save(envio);
        return EnvioDTO.fromEntity(envioGuardado);
    }

    @PutMapping("/{id}") // Actualizar
    public EnvioDTO updateEnvio(@PathVariable String id, @RequestBody EnvioDTO envioDTO){
        Envio envio = envioDTO.toEntity();
        Envio envioActualizado = envioService.update(id,envio);
        return EnvioDTO.fromEntity(envioActualizado);
    }


    @DeleteMapping("/{id}")
    public void deleteEnvio(@PathVariable String id){ //@PatchMapping
        envioService.deleteById(id);
    }

}
